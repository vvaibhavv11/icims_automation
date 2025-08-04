
from playwright.async_api import async_playwright, Locator,Page
from playwright_stealth import Stealth
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from prompt import SYSTEM_PROMPT
import asyncio
from core import click_accept_cookies, extract_fields, enter_data_into_form, Item, b64
import time


async def determine_which_button_to_click(buttons: list[Locator]) -> str:
    fields = []
    for button in buttons:
        button_value = await button.get_attribute("value")
        fields.append(button_value)
    result = await Agent(model, system_prompt="now you have the array of button label give the label that will lead us to the next page like submit and just return the string", output_type=str).run(f"button_values: {fields}")
    print(f"Determined button to click: {result.output}")
    return result.output

provider = GoogleProvider(api_key='AIzaSyDoEFuBTh_36lBZD9ekFn0kQByVJiSjBsA')
model = GoogleModel('gemini-2.5-flash', provider=provider)
Profile_agent = Agent(model, system_prompt=SYSTEM_PROMPT, output_type=list[Item])

async def click_next_page_button(page: Page) -> bool:
    try:
        frame_locator = page.frame_locator("iframe#icims_content_iframe")
        await frame_locator.locator("form").wait_for(state="attached")
        form = frame_locator.locator("form")
        next_button = await form.locator("input[type='submit']").all()
        time.sleep(3)
        print("Checking for 'Next' button...")
        print(f"next button {next_button}")
        if next_button:
            button_val = await determine_which_button_to_click(next_button)
            if not button_val:
                print("No valid button found to click.")
                return False
            async with page.expect_navigation():
                submit_button = form.locator(f"input[type='submit'][value='{button_val}']")
                submit_button = await submit_button.click()
                return True
        else:
            print("'Next' button not found.")
            return False
    except:
        first_iframe = page.frame_locator("iframe#icims_content_iframe")
        second_iframe = first_iframe.frame_locator("iframe#icims_formFrame")
        await second_iframe.locator("form").wait_for(state="attached")
        form = second_iframe.locator("form")
        next_button = await form.locator("input[type='submit']").all()
        time.sleep(3)
        print("Checking for 'Next' button...")
        print(f"next button {next_button}")
        if next_button:
            button_val = await determine_which_button_to_click(next_button)
            if not button_val:
                print("No valid button found to click.")
                return False
            async with page.expect_navigation():
                submit_button = form.locator(f"input[type='submit'][value='{button_val}']")
                submit_button = await submit_button.click()
                return True
        else:
            print("'Next' button not found.")
            return False


async def hendle_cookie_banner(page: Page):
    _ = await click_accept_cookies(page)

async def click_apply_button(page: Page):
    accept_button = page.locator("a",has_text="Apply")
    print("Checking for 'Apply' button...")
    # await accept_button.wait_for(state="visible", timeout=5000)
    if await accept_button.count() > 0:
        await accept_button.click()
        print("Clicked 'Apply' button.")

async def wait_for_page_load(page: Page):
    try:
        await page.wait_for_load_state("load")
        frame_locator = page.frame_locator("iframe#icims_content_iframe")
        await frame_locator.locator("form").wait_for(state="attached")
    except Exception as e:
        print(f"Error waiting for page load: {e}")
    

async def ask_ai(fields: str, b64: bytes) -> list[Item]:
    """Ask the AI to fill the fields based on the resume."""
    response = await Profile_agent.run(
        [
            "You are given a resume and a json object of fields, fill the fields with the answers from the resume.",
            f"Here is the fields to fill: {fields}",
            "Here is the resume in base64 format:",
            BinaryContent(data=b64, media_type="application/pdf"),
        ]
    )
    print("AI response:", response.output)
    return response.output

async def main():
    try:
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch_persistent_context(user_data_dir="/home/vaibhav/.config/chromium", headless=False,args=['--disable-blink-features=AutomationControlled'])
            page = await browser.new_page()
            job_url = "https://careers.amd.com/careers-home/jobs/67789?lang=en-us"
            await page.goto(job_url)
            await page.wait_for_load_state("load")
            await hendle_cookie_banner(page)
            await click_apply_button(page)
            while True:
                await wait_for_page_load(page)
                await hendle_cookie_banner(page)
                fields = await extract_fields(page)
                # print(f"Extracted fields: {fields}")
                fields_ans = await ask_ai(fields, b64)
                await enter_data_into_form(page, fields=fields_ans)
                nextEl = await click_next_page_button(page);
                if not nextEl:
                    print("No more pages to navigate.")
                    break
                time.sleep(2)  # Wait for the next page to load
            time.sleep(20)
            await browser.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())