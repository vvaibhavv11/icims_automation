from playwright.sync_api import sync_playwright
from playwright.sync_api import FrameLocator,Page
from pydantic_ai import Agent, BinaryContent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic import BaseModel
import nest_asyncio
import time
from prompt import SYSTEM_PROMPT
nest_asyncio.apply()


with open("/mnt/a/downloads/Lin_Mei_Experiened_Level_Software.pdf", "rb") as f:
    b64 = f.read()

class Item(BaseModel):
    label: str
    type: str
    id: str
    answer: str 

provider = GoogleProvider(api_key='AIzaSyDoEFuBTh_36lBZD9ekFn0kQByVJiSjBsA')
model = GoogleModel('gemini-2.5-pro', provider=provider)
Profile_agent = Agent(model, system_prompt=SYSTEM_PROMPT, deps_type= Page, output_type=bool)
# agent = Agent(  
#     'google-gla:gemini-2.5-pro',
#     system_prompt='Be concise, reply with one sentence.',
# )


def extract_fields(page: FrameLocator):
    controls = {
        "text": page.locator("input[type='text'],textarea"),
        # "multiselect": page.locator("select[multiple]"),
        "select": page.locator('select:not([class*="dropdown-hide"])'),
        "special_select": page.locator('select[class*="dropdown-hide"]'),
        "checkbox": page.locator("input[type='checkbox']"),
        "date": page.locator("input[type='date']"),
        "file": page.locator("input[type='file']"),
        "radio": page.locator("input[type='radio']")
    }
    print("Extracting fields from the page...")
    results = []
    for typ, locator in controls.items():
        for elem in locator.all():
            id = elem.get_attribute('id');
            if not id:
                continue
            label = page.locator(f"label[for='{id}']").first.inner_text()
            # results.append({
            #     "label": label.strip(),
            #     "id": elem.get_attribute("id"),
            #     "type": typ,
            #     "options": None  # Placeholder for options if needed
            # })
            # print(f"Processing {typ} field with id: {elem.get_attribute('id')}")
            # label = page.locator(f"label[for='{elem.get_attribute('id')}']").inner_text()
            # print(f"Found {typ} field with label: {label.strip()}")
            options = None
            if typ == "multiselect":
                options = [o.inner_text() for o in elem.locator("option").all()]
            elif typ == "checkbox":
                options = [o.inner_text() for o in elem.locator("label").all()]
            elif typ == "radio":
                options = [o.inner_text() for o in elem.locator("label").all()]
            elif typ == "file":
                options = [elem.get_attribute("accept")]
            elif typ == "date":
                options = [elem.get_attribute("min"), elem.get_attribute("max")]
            elif typ == "text":
                options = [elem.get_attribute("placeholder")]
            elif typ == "multiselect" or typ == "dropdown":
                options = [o.inner_text() for o in elem.locator("option").all()]
            elif typ == "special_select":
                # print(f"{elem}")
                count = 0
                options = []
                while True:
                    option = [o.inner_text() for o in page.locator(f"li[id=\"result-selectable_{id}_{count}\"]").all()]
                    count += 1
                    options = [*options, *option]
                    if not option:
                        break
                print(f"Found select field with options: {options} for field {label.strip()}")
            elif typ == "select":
                options = [o.inner_text() for o in elem.locator("option").all()]
                print(f"Found select field with options: {options} for field {label.strip()}")
            # print(f"Extracted {typ} field: {label.strip()} with id: {elem.get_attribute('id')}")
            results.append({
                "label": label.strip(),
                "id": elem.get_attribute("id"),
                "type": typ,
                "options": options
            })
    return results


def enter_data_into_form(page: FrameLocator, fields: list[Item]):
    print("Entering data into the form...")
    for field in fields:
        if field.type == "text":
            input_elem = page.locator(f"input[type='text'][id='{field.id}'], textarea[id='{field.id}']")
            if input_elem.count() > 0:
                input_elem.first.fill(field.answer)
                print(f"Filled text field {field.label} with value: {field.answer}")
        elif field.type == "multiselect":
            select_elem = page.locator(f"select[multiple][id='{field.id}']")
            if select_elem.count() > 0:
                options = select_elem.locator("option")
                for option in options.all():
                    if option.inner_text() in field.answer:
                        option.set_checked(True)
                print(f"Selected options in multiselect field {field.label}: {field.answer}")
        elif field.type == "select":
            select_elem = page.locator(f"select[id='{field.id}']")
            if select_elem.count() > 0:
                select_elem.first.select_option(value=field.answer)
                print(f"Selected option in select field {field.label}: {field.answer}")
        elif field.type == "checkbox":
            checkbox_elem = page.locator(f"input[type='checkbox'][id='{field.id}']")
            if checkbox_elem.count() > 0:
                checkbox_elem.set_checked(field.answer == "true")
                print(f"Set checkbox field {field.label} to: {field.answer}")
        elif field.type == "radio":
            radio_elems = page.locator(f"input[type='radio'][name='{field.id}']")
            for radio in radio_elems.all():
                if radio.get_attribute("value") == field.answer:
                    radio.check()
                    print(f"Checked radio button in field {field.label} with value: {field.answer}")
        elif field.type == "date":
            date_elem = page.locator(f"input[type='date'][id='{field.id}']")
            if date_elem.count() > 0:
                date_elem.fill(field.answer)
                print(f"Filled date field {field.label} with value: {field.answer}")
        elif field.type == "file":
            file_input = page.locator(f"input[type='file'][id='{field.id}']")
            if file_input.count() > 0:
                file_input.set_input_files(field.answer)
                print(f"Uploaded file to field {field.label}: {field.answer}")
        elif field.type == "special_select":
            special_select_elem = page.locator(f"span[id='{field.id}_fakeSelected_icimsDropdown']")
            if special_select_elem.count() > 0:
                special_select_elem.evaluate('(element, html) => element.innerHTML = html', field.answer)


@Profile_agent.tool
def click_accept_cookies(c: RunContext[Page]) -> bool:
    try:
        accept_button = c.deps.get_by_text("Accept Cookies")
        if accept_button.count() > 0:
            accept_button.first.click()
            print("Accepted cookies")
            return True
        else:
            print("No 'Accept Cookies' button found")
            return False
    except Exception as e:
        print(f"Error accepting cookies: {e}")
        return False


@Profile_agent.tool
def get_screenshot(c: RunContext[Page]) -> BinaryContent:
    screenshot = c.deps.screenshot(full_page=True)
    return BinaryContent(data=screenshot, media_type="image/png")



with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    job_url = "https://careers-amd.icims.com/jobs/67789/software-development-engineer%2c-ai-infrastructure/candidate?from=login&eem=WukLBjV8DiPyZNWyAuQ8Y-40MlIuHTwlZlQyvFknwClxkIAcOFJZr_9bADBXJ1X5&code=97a90988fce5805d06a2ffa627a8356fe8b538b41f980dd2717389ff6022c4de&ga=afded2fc947dce5363714b12c9a0b757b2e85103995f9bf923150b5e4a474891&accept_gdpr=1"
    page.goto(job_url)


    # Wait until iframe is present
    page.wait_for_selector("iframe#icims_content_iframe", timeout=30000, state="attached")
    # page.wait_for_load_state("domcontentloaded")
    # frame_locator = page.frame_locator("iframe")
    # frame_locator = page.frame_locator("iframe#icims_content_iframe")

    # Wait for the form to be visible before starting the loop
    # frame_locator.locator("form").locator("input[type='text']").all()
    # frame_locator.locator("form").wait_for(state="visible")
    screenshort = page.screenshot(full_page=True)
    print("Form is ready, starting to fill inputs...")
    # fields = extract_fields(frame_locator)
    # print("Fields extracted:", fields)
    # print(frame_locator.locator("form").locator("input[type='text']").all())
        # DocumentUrl(url="file:///mnt/a/downloads/Lin%20Mei_Experiened%20Level%20Software.pdf"),


    result = Profile_agent.run_sync(
        [
            "inial screenshot",
            BinaryContent(data=screenshort, media_type="image/png"),

        ],
        deps=page
    )
    print(result.output)

    # enter_data_into_form(frame_locator, result.output)

    print("Form filled")

    # time.sleep(30)  

    browser.close()

