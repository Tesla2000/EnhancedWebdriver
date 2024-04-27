from time import sleep
from typing import Optional

import chromedriver_autoinstaller
from retry import retry
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
from undetected_chromedriver import ChromeOptions


class EnhancedWebdriver(WebDriver):
    """Webdriver with added functions that can decrease boilerplates.

    :class:`EnhancedWebDriver` extends :class:`WebDriver` with additional features.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise ValueError(
            "__init__ function of EnhancedWebdriver shouldn't be used."
            " Use EnhancedWebdriver.create to create driver instance."
        )

    @classmethod
    def create(
        cls,
        web_driver: Optional[WebDriver] = None,
        undetected: bool = False,
        options: ChromeOptions = None,
        service: Service = None,
        keep_alive: bool = True,
    ) -> "EnhancedWebdriver":
        """
        Create an instance of EnhancedWebDriver.

        :param web_driver: An optional instance of WebDriver.[WebDriver], optional
        :param undetected: Whether to run an instance of UndetectedChromedriver
        :param keep_alive: Whether to configure ChromeRemoteConnection to use HTTP keep-alive
        :param service: Service object for handling the browser driver if you need to pass extra details
        :param options: this takes an instance of ChromeOptions
        :return: An instance of EnhancedWebDriver.

        """
        instance = object.__new__(EnhancedWebdriver)
        if web_driver is None:
            chromedriver_autoinstaller.install()
            if not undetected:
                web_driver = webdriver.Chrome(
                    options=options, service=service, keep_alive=keep_alive
                )
            else:
                import undetected_chromedriver as uc

                web_driver = uc.Chrome(options=options, service_args=service, keep_alive=keep_alive)
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

    @retry(tries=5, delay=1)
    def get_text_of_element(self, value: str, by: By = By.XPATH, seconds=1) -> str:
        """
        Get the visible (i.e., not hidden by CSS) innerText of this element.

        :param value: Locator value of the element.
        :param by: Locator strategy, defaults to By.XPATH.
        :param seconds: Maximum time to wait for the element, defaults to 1.
        :return: The innerText of the element.

        """
        elem = self._wait(value, seconds, by)
        return elem.text or elem.get_attribute("textContent")

    @retry(tries=5, delay=1)
    def is_element_present(
        self, value: str, seconds: float = 1, by: By = By.XPATH
    ) -> bool:
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

    @retry(tries=5, delay=1)
    def is_element_selected(
        self, value: str, seconds: float = 1, by: By = By.XPATH
    ) -> bool:
        """
        Determine if the element is selected or not.

        :param value: Locator value of the element.
        :param seconds: Maximum time to wait for the element, defaults to 1.
        :param by: Locator strategy, defaults to By.XPATH.
        :return: True if the element is selected, False otherwise.

        """
        return self._wait(value, seconds, by).is_selected()

    @retry(tries=5, delay=1)
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

    @retry(tries=5, delay=1)
    def get_all_elements(self, element, by: By = By.XPATH):
        """
        Find all elements within the current context using the given mechanism.

        :param element: Locator value of the element.
        :param by: Locator strategy, defaults to By.XPATH.
        :return: A list of all WebElements matching the criteria.

        """
        return self.find_elements(by=by, value=element)

    @retry(tries=5, delay=1)
    def write(
        self, value: str, keys: str, sleep_function=None, by: By = By.XPATH, time=10
    ) -> bool:
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

    @retry(tries=5, delay=1)
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

    @retry(tries=5, delay=1)
    def wait_and_click_js(self, value: str, time=1, by: By = By.XPATH):
        """
        Wait for an element to be present in the DOM and click using JavaScript.

        :param value: Locator value of the element.
        :param time: Maximum time to wait for the element, defaults to 1.
        :param by: Locator strategy, defaults to By.XPATH.

        """
        element = self._wait(value, time, by)
        self.execute_script("arguments[0].click();", element)

    @retry(tries=5, delay=1)
    def get_canvas(self, canvas_path: str = "//canvas"):
        """
        Get a screenshot of the canvas.

        :param canvas_path: Locator value of the canvas element, defaults to "//canvas".
        :return: Screenshot of the canvas.

        """
        canvas = self._wait(canvas_path)
        return canvas.screenshot_as_png

    @retry(tries=5, delay=1)
    def click_on_canvas(
        self,
        offset_x: int,
        offset_y: int,
        canvas_path: str = "//canvas",
        right_click: bool = False,
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

    @retry(tries=5, delay=1)
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
