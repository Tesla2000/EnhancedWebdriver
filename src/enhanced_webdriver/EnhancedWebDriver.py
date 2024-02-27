import os
import platform
import re
import shutil
import urllib
import zipfile
from pathlib import Path
from time import sleep
from typing import Optional, Union

import requests
from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    ElementClickInterceptedException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


class EnhancedWebDriver(WebDriver):
    @classmethod
    def create(
        cls,
        web_driver: Optional[WebDriver] = None,
        executable_path: Union[Path, str] = None,
    ) -> "EnhancedWebDriver":
        instance = object.__new__(EnhancedWebDriver)
        if web_driver is None:
            if executable_path is None:
                executable_path = Path(__file__).parent / "driver.exe"
            if not Path(executable_path).exists():
                cls._download_new_driver(executable_path)
            service = Service(executable_path=executable_path)
            web_driver = webdriver.Chrome(service=service)
        instance.__dict__ = web_driver.__dict__
        return instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    @staticmethod
    def _get_current_driver_version() -> str:
        return re.findall(
            r"[\w./:]+chrome-for-testing-public/[\d+.]+",
            requests.get(
                "https://googlechromelabs.github.io/chrome-for-testing/#stable"
            ).content.decode(),
        )[0]

    @classmethod
    def _download_new_driver(cls, executable_path: Path):
        system = platform.system().lower().replace("dows", "")
        machine = re.findall(r"\d+", platform.machine())[-1]
        urllib.request.urlretrieve(
            "{}/{}{}/chromedriver-{}{}.zip".format(cls._get_current_driver_version(), system, machine, system, machine),
            executable_path.with_suffix(".zip"),
        )
        with zipfile.ZipFile(executable_path.with_suffix(".zip")) as zip_ref:
            zip_ref.extractall(executable_path)
        shutil.move(
            next(next(executable_path.glob("*")).glob("c*")), executable_path.parent
        )
        shutil.rmtree(executable_path.parent.joinpath("driver.exe"))
        os.remove(executable_path.with_suffix(".zip"))
        os.rename(next(executable_path.parent.glob("chromedrive*")), executable_path)
        current_permissions = os.stat(executable_path).st_mode
        new_permissions = current_permissions | 0o111
        os.chmod(executable_path, new_permissions)

    def wait(self, value, seconds=1, by=By.XPATH):
        self.implicitly_wait(seconds)
        element = self.find_element(by, value)
        sleep(0.5)
        return element

    def get_text_of_element(self, value, by=By.XPATH, seconds=1):
        return self.wait(value, seconds, by).text

    def is_element_present(self, value, seconds=1, by=By.XPATH):
        try:
            self.wait(value, seconds, by)
            return True
        except NoSuchElementException:
            return False

    def is_element_selected(self, value, seconds=1, by=By.XPATH) -> bool:
        return self.wait(value, seconds, by).is_selected()

    def get_attribute(self, value, dtype, by=By.XPATH, seconds=10):
        return self.wait(value, seconds, by).get_attribute(dtype)

    def get_all_elements(self, element, by=By.XPATH):
        return self.find_elements(by=by, value=element)

    def write(self, value, keys, sleep_function=None, by=By.XPATH, time=10) -> bool:
        try:
            element = self.wait(value, time, by)
            element.clear()
            element.send_keys(str(keys))
            if sleep_function:
                sleep_function()
        except WebDriverException:
            return False
        return True

    def click(self, value, sleep_function=None, by=By.XPATH, seconds=1):
        try:
            element = self.wait(value, seconds, by)
            WebDriverWait(self, seconds).until(
                expected_conditions.element_to_be_clickable(element)
            ).click()

            if sleep_function:
                sleep_function()
        except ElementClickInterceptedException:
            sleep(0.01)
            WebDriverWait(self, seconds).until(
                expected_conditions.element_to_be_clickable(
                    self.wait(value, seconds, by)
                )
            ).click()
        except (
            NoSuchElementException,
            TimeoutException,
            StaleElementReferenceException,
        ) as _:
            return False
        return True

    def wait_and_click_js(self, value, time=1, by=By.XPATH):
        element = self.wait(value, time, by)
        self.execute_script("arguments[0].click();", element)

    def get_canvas(self, canvas_path="//canvas"):
        canvas = self.wait(canvas_path)
        return canvas.screenshot_as_png

    def click_on_canvas(
        self, offset_x, offset_y, canvas_path="//canvas", right_click=False
    ):
        canvas = self.wait(canvas_path)
        if right_click:
            ActionChains(self).move_to_element(canvas).move_by_offset(
                offset_x, offset_y
            ).context_click().release().perform()
        else:
            ActionChains(self).move_to_element(canvas).move_by_offset(
                offset_x, offset_y
            ).click().release().perform()

    def scroll_down(self):
        self.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        sleep(0.5)

    def scroll_up(self):
        self.execute_script("window.scrollTo(0,-250)")
        sleep(0.5)
