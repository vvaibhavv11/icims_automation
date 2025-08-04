from playwright.async_api import Page,TimeoutError as PlaywrightTimeoutError, Locator
from pydantic import BaseModel
import time
from prompt import SYSTEM_PROMPT


with open("/mnt/a/downloads/Lin_Mei_Experiened_Level_Software.pdf", "rb") as f:
    b64 = f.read()

class Item(BaseModel):
    label: str
    type: str
    id: str
    answer: str 


async def extract_fields(page: Page):
    try:
        frame_locator = page.frame_locator("iframe#icims_content_iframe")
        await frame_locator.locator("form").wait_for(state="attached")
        form = frame_locator.locator("form")
        return await form.inner_html()
    except PlaywrightTimeoutError:
        print(f"Error extracting fields: {PlaywrightTimeoutError}")
        first_iframe = page.frame_locator("iframe#icims_content_iframe")
        second_iframe = first_iframe.frame_locator("iframe#icims_formFrame")
        await second_iframe.locator("form").wait_for(state="attached")
        form = second_iframe.locator("form")
        return await form.inner_html()

""""
this is the old way to the extaction of the filed not very efficient and not very good
but it works for some cases, so I will keep it here for now
but he best way is to just give the html directly to the ai and let it extract the fields
for that we are using the extract_fields function above
"""
async def old_extract_fields(page: Page):
    frame_locator = page.frame_locator("iframe#icims_content_iframe")
    await frame_locator.locator("form").wait_for(state="attached")
    form = frame_locator.locator("form")
    controls = {
        "text": form.locator("input[type='text']"),
        "email": form.locator("input[type='email']"),
        # "multiselect": page.locator("select[multiple]"),
        "select": form.locator('select:not([class*="dropdown-hide"])'),
        "special_select": form.locator('select[class*="dropdown-hide"]'),
        "checkbox": form.locator("input[type='checkbox']"),
        "date": form.locator("input[type='date']"),
        "file": form.locator("input[type='file']"),
        "radio": form.locator("input[type='radio']")
    }
    print("Extracting fields from the page...")
    results = []
    for typ, locator in controls.items():
        for elem in await locator.all():
            id = await elem.get_attribute('id');
            if not id or id == "rcf3049_Text":
                continue
            print(f"Processing element with id: {id} of type: {typ}")
            # print(f"elemnet {elem} ")

            label = await form.locator(f"label[for='{id}']").first.inner_text()
            options = None
            if typ == "multiselect":
                options = [await o.inner_text() for o in await elem.locator("option").all()]
            elif typ == "checkbox":
                options = [await o.inner_text() for o in await elem.locator("label").all()]
            elif typ == "radio":
                options = [await o.inner_text() for o in await elem.locator("label").all()]
            elif typ == "file":
                options = [await elem.get_attribute("accept")]
            elif typ == "date":
                options = [await elem.get_attribute("min"), await elem.get_attribute("max")]
            elif typ == "text":
                options = [await elem.get_attribute("placeholder")]
            elif typ == "email":
                options = [await elem.get_attribute("placeholder")]
            elif typ == "multiselect" or typ == "dropdown":
                options = [await o.inner_text() for o in await elem.locator("option").all()]
            elif typ == "special_select":
                # print(f"{elem}")
                count = 0
                options = []
                while True:
                    option = [await o.inner_text() for o in await form.locator(f"li[id=\"result-selectable_{id}_{count}\"]").all()]
                    count += 1
                    options = [*options, *option]
                    if not option:
                        break
            elif typ == "select":
                options = [await o.inner_text() for o in await elem.locator("option").all()]
            results.append({
                "label": label.strip(),
                "id": id,
                "required": await elem.get_attribute("i_required") is not None,
                "type": typ,
                "options": options
            })
    return results

async def enter_data(form: Locator, fields: list[Item]):
    for field in fields:
        if field.type == "text":
            input_elem = form.locator(f"input[type='text'][id='{field.id}'], textarea[id='{field.id}']")
            if await input_elem.count() > 0:
                await input_elem.first.fill(field.answer)
                print(f"Filled text field {field.label} with value: {field.answer}")
        elif field.type == "email":
            email_elem = form.locator(f"input[id='{field.id}']")
            if await email_elem.count() > 0:
                print(f"Filling email field {field.label} with value: {field.answer}")
                await email_elem.first.fill(field.answer)
                print(f"Filled email field {field.label} with value: {field.answer}")
        elif field.type == "multiselect":
            select_elem = form.locator(f"select[multiple][id='{field.id}']")
            if await select_elem.count() > 0:
                options = select_elem.locator("option")
                for option in await options.all():
                    if await option.inner_text() in field.answer:
                        await option.set_checked(True)
                print(f"Selected options in multiselect field {field.label}: {field.answer}")
        elif field.type == "select":
            select_elem = form.locator(f"select[id='{field.id}']")
            if await select_elem.count() > 0:
                await select_elem.first.select_option(value=field.answer)
                print(f"Selected option in select field {field.label}: {field.answer}")
        elif field.type == "checkbox":
            checkbox_elem = form.locator(f"input[id='{field.id}']")
            if await checkbox_elem.count() > 0:
                print(f"Setting checkbox field {field.label} to: {field.answer}")
                await checkbox_elem.set_checked(field.answer == "true")
                print(f"Set checkbox field {field.label} to: {field.answer}")
        elif field.type == "radio":
            radio_elems = form.locator(f"input[type='radio'][name='{field.id}']")
            for radio in await radio_elems.all():
                if radio.get_attribute("value") == field.answer:
                    await radio.check()
                    print(f"Checked radio button in field {field.label} with value: {field.answer}")
        elif field.type == "date":
            date_elem = form.locator(f"input[type='date'][id='{field.id}']")
            if await date_elem.count() > 0:
                await date_elem.fill(field.answer)
                print(f"Filled date field {field.label} with value: {field.answer}")
        elif field.type == "file":
            file_input = form.locator(f"input[type='file'][id='{field.id}']")
            if await file_input.count() > 0:
                await file_input.set_input_files(files=[{"name": "resume.pdf", "mimeType": "application/pdf", "buffer": b64}])
                time.sleep(20)
                print(f"Uploaded file to field {field.label}: {field.answer}")
        elif field.type == "special_select":
            special_select_elem = form.locator(f"span[id='{field.id}_fakeSelected_icimsDropdown']")
            if await special_select_elem.count() > 0:
                await special_select_elem.evaluate('(element, html) => element.innerHTML = html', field.answer)
                print(f"set special_select to field {field.label} with the valuse: {field.answer}")


async def enter_data_into_form(page: Page, fields: list[Item]):
    try:
        frame_locator = page.frame_locator("iframe#icims_content_iframe")
        await frame_locator.locator("form").wait_for(state="attached")
        form = frame_locator.locator("form")
        await enter_data(form, fields)
    except:
        first_iframe = page.frame_locator("iframe#icims_content_iframe")
        second_iframe = first_iframe.frame_locator("iframe#icims_formFrame")
        await second_iframe.locator("form").wait_for(state="attached")
        form = second_iframe.locator("form")
        await enter_data(form, fields)



async def click_accept_cookies(page: Page) -> bool:
    try:
        accept_button = page.locator("button",has_text="Accept Cookies")
        print("Checking for 'Accept Cookies' button...")
        # await accept_button.wait_for(state="visible", timeout=5000)
        if await accept_button.count() > 0:
            await accept_button.click()
            print("Accepted cookies")
            return True
        else:
            print("No 'Accept Cookies' button found")
            return False
    except Exception as e:
        print(f"Error accepting cookies: {e}")
        return False
