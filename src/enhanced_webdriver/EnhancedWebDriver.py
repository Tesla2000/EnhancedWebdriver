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
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


class EnhancedWebDriver(WebDriver):
    """Webdriver with added functions that can decrease boilerplates. 

    :class:`EnhancedWebDriver` extends :class:`WebDriver` with additional features.

    """

    @classmethod
    def create(
        cls,
        web_driver: Optional[WebDriver] = None,
        executable_path: Union[Path, str] = None,
    ) -> "EnhancedWebDriver":
        """
        Create an instance of EnhancedWebDriver.

        :param web_driver: An optional instance of WebDriver.[WebDriver], optional
        :param executable_path: Path to the webdriver executable.[Path, str], optional
        :return: An instance of EnhancedWebDriver.

        """
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
        """
        Enter the context.

        :return: The instance itself.

        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context.

        :param exc_type: The type of exception.
        :param exc_val: The exception value.
        :param exc_tb: The traceback.

        """
        self.quit()

    def get_text_of_element(self, value: str, by: By = By.XPATH, seconds=1) -> str:
        """
        Get the visible (i.e., not hidden by CSS) innerText of this element.

        :param value: Locator value of the element.
        :param by: Locator strategy, defaults to By.XPATH.
        :param seconds: Maximum time to wait for the element, defaults to 1.
        :return: The innerText of the element.

        """
        return self._wait(value, seconds, by).text

    def is_element_present(self, value: str, seconds: float = 1, by: By = By.XPATH) -> bool:
        """
        Check if an element is present in the DOM.

        :param value: Locator value of the element.
        :param seconds: Maximum time to wait for the element, defaults to 1.
        :param by: Locator strategy, defaults to By.XPATH.
        :return: True if element is present, False otherwise.

        """
        try:
            self._wait(value, seconds, by)
            return True
        except NoSuchElementException:
            return False

    def is_element_selected(self, value: str, seconds: float = 1, by: By = By.XPATH) -> bool:
        """
        Determine if the element is selected or not.

        :param value: Locator value of the element.
        :param seconds: Maximum time to wait for the element, defaults to 1.
        :param by: Locator strategy, defaults to By.XPATH.
        :return: True if the element is selected, False otherwise.

        """
        return self._wait(value, seconds, by).is_selected()

    def get_attribute(self, value: str, dtype: str, by: By = By.XPATH, seconds=10):
        """
        Get the value of the specified attribute of the element.

        :param value: Locator value of the element.
        :param dtype: Name of the attribute to retrieve.
        :param by: Locator strategy, defaults to By.XPATH.
        :param seconds: Maximum time to wait for the element, defaults to 10.
        :return: The value of the attribute.

        """
        return self._wait(value, seconds, by).get_attribute(dtype)

    def get_all_elements(self, element, by: By = By.XPATH):
        """
        Find all elements within the current context using the given mechanism.

        :param element: Locator value of the element.
        :param by: Locator strategy, defaults to By.XPATH.
        :return: A list of all WebElements matching the criteria.

        """
        return self.find_elements(by=by, value=element)

    def write(self, value: str, keys: str, sleep_function=None, by: By = By.XPATH, time=10) -> bool:
        """
        Simulate typing into the element.

        :param value: Locator value of the element.
        :param keys: The text to be typed.
        :param sleep_function: Function to execute after typing.
        :param by: Locator strategy, defaults to By.XPATH.
        :param time: Maximum time to wait for the element, defaults to 10.
        :return: True if typing was successful, False otherwise.

        """
        try:
            element = self._wait(value, time, by)
            element.clear()
            element.send_keys(str(keys))
            if sleep_function:
                sleep_function()
        except WebDriverException:
            return False
        return True

    def click(self, value: str, sleep_function=None, by: By = By.XPATH, seconds=1):
        """
        Click on an element.

        :param value: Locator value of the element.
        :param sleep_function: Function to execute after clicking.
        :param by: Locator strategy, defaults to By.XPATH.
        :param seconds: Maximum time to wait for the element, defaults to 1.
        :return: True if click was successful,

        """
        try:
            element = self._wait(value, seconds, by)
            WebDriverWait(self, seconds).until(
                expected_conditions.element_to_be_clickable(element)
            ).click()

            if sleep_function:
                sleep_function()
        except ElementClickInterceptedException:
            sleep(0.01)
            WebDriverWait(self, seconds).until(
                expected_conditions.element_to_be_clickable(
                    self._wait(value, seconds, by)
                )
            ).click()
        except (
            NoSuchElementException,
            TimeoutException,
            StaleElementReferenceException,
        ) as _:
            return False
        return True

    def wait_and_click_js(self, value: str, time=1, by: By = By.XPATH):
        """
        Wait for an element to be present in the DOM and click using JavaScript.

        :param value: Locator value of the element.
        :param time: Maximum time to wait for the element, defaults to 1.
        :param by: Locator strategy, defaults to By.XPATH.

        """
        element = self._wait(value, time, by)
        self.execute_script("arguments[0].click();", element)

    def get_canvas(self, canvas_path: str = "//canvas"):
        """
        Get a screenshot of the canvas.

        :param canvas_path: Locator value of the canvas element, defaults to "//canvas".
        :return: Screenshot of the canvas.

        """
        canvas = self._wait(canvas_path)
        return canvas.screenshot_as_png

    def click_on_canvas(
        self, offset_x: int, offset_y: int, canvas_path: str = "//canvas", right_click: bool = False
    ):
        """
        Click on a specific location on the canvas.

        :param offset_x: X-coordinate offset.
        :param offset_y: Y-coordinate offset.
        :param canvas_path: Locator value of the canvas element, defaults to "//canvas".
        :param right_click: Whether to perform a right click, defaults to False.

        """
        canvas = self._wait(canvas_path)
        if right_click:
            ActionChains(self).move_to_element(canvas).move_by_offset(
                offset_x, offset_y
            ).context_click().release().perform()
        else:
            ActionChains(self).move_to_element(canvas).move_by_offset(
                offset_x, offset_y
            ).click().release().perform()

    def scroll_down(self):
        """Scroll down the webpage."""
        self.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        sleep(0.5)

    def scroll_up(self):
        """Scroll up the webpage."""
        self.execute_script("window.scrollTo(0,-250)")
        sleep(0.5)

    @staticmethod
    def _get_current_driver_version() -> str:
        """
        Fetch the current Chrome driver version.

        :return: Current Chrome driver version.

        """
        return re.findall(
            r"[\w\./:]+chrome-for-testing-public/[\d+\.]+",
            requests.get(
                "https://googlechromelabs.github.io/chrome-for-testing/#stable"
            ).content.decode(),
        )[0]

    @classmethod
    def _download_new_driver(cls, executable_path: Path) -> None:
        """
        Download and install the latest Chrome driver.

        :param executable_path: Path to store the downloaded driver.

        """
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

    def _wait(self, value: str, seconds: float = 1, by: By = By.XPATH) -> WebElement:
        """
        Wait for an element to be present in the DOM and return it.

        :param value: Locator value of the element.
        :param seconds: Maximum time to wait for the element, defaults to 1.
        :param by: Locator strategy, defaults to By.XPATH.
        :return: The located element.

        """
        self.implicitly_wait(seconds)
        element = self.find_element(by, value)
        sleep(0.5)
        return element
