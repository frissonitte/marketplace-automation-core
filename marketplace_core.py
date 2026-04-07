import logging
import time
from dataclasses import dataclass
from typing import Optional

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from target_profiles import load_target_profile

TARGET_PROFILE = load_target_profile("mobile_market_primary")
TARGET_APPIUM = TARGET_PROFILE["appium"]
TARGET_SELECTORS = TARGET_PROFILE["selectors"]
TARGET_TEXTS = TARGET_PROFILE["texts"]
TARGET_LOGGING = TARGET_PROFILE["logging"]

PRODUCT_TITLE_IDS = tuple(TARGET_SELECTORS["product_title_ids"])
PRODUCT_LIST_READY_IDS = tuple(TARGET_SELECTORS["product_list_ready_ids"])
STICKY_BUTTONS_ID = TARGET_SELECTORS["sticky_buttons_id"]
EARNING_PRICE_XPATH = TARGET_SELECTORS["earning_price_xpath"]
EARNING_PRICE_SUBMIT_XPATH = TARGET_SELECTORS["earning_price_submit_xpath"]
BOTTOM_NAV_PRODUCTS_ID = TARGET_SELECTORS["bottom_nav_products_id"]
FILTER_BUTTON_ID = TARGET_SELECTORS["filter_button_id"]
SORT_AREA_ID = TARGET_SELECTORS["sort_area_id"]
DESCRIPTION_INPUT_ID = TARGET_SELECTORS["description_input_id"]
PRICE_INPUT_ID = TARGET_SELECTORS["price_input_id"]
APPROVAL_BUTTON_ID = TARGET_SELECTORS["approval_button_id"]
SORT_LOWEST_PRICE_XPATH = TARGET_SELECTORS["sort_lowest_price_xpath"]
PRODUCTS_TAB_TEXT = TARGET_TEXTS["products_tab"]


@dataclass(frozen=True)
class MarketplaceBotConfig:
    appium_url: str = "http://localhost:4723"
    platform_name: str = TARGET_APPIUM["platform_name"]
    device_name: str = TARGET_APPIUM["device_name"]
    app_package: str = TARGET_APPIUM["app_package"]
    automation_name: str = TARGET_APPIUM["automation_name"]
    no_reset: bool = TARGET_APPIUM["no_reset"]

    wait_seconds: int = 15
    post_action_sleep_s: float = 1.5
    max_scrolls_without_new_items: int = 3

    edit_button_x: int = 1024
    edit_button_y: int = 1850

    back_to_list_x: Optional[int] = None
    back_to_list_y: Optional[int] = None

    enable_sort_lowest_price: bool = False
    enable_description_update: bool = False

    enable_price_drop: bool = False 

    description_old_text: str = "PLACEHOLDER TEXT HERE"
    description_new_text: str = "PLACEHOLDER TEXT HERE"

    log_file: str = TARGET_LOGGING["log_file"]


def setup_logging(log_file: str) -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _tap_xy(driver, x: int, y: int, duration_ms: int = 250) -> None:
    try:
        driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
        return
    except Exception:
        pass

    try:
        driver.tap([(x, y)], duration_ms)
        return
    except Exception:
        raise


def _press_back(driver) -> None:
    driver.press_keycode(4)


def _press_enter(driver) -> None:
    driver.press_keycode(66)


def _element_text(element) -> str:
    return (element.text or element.get_attribute("text") or "").strip()


def _element_center(element) -> tuple[int, int]:
    rect = element.rect
    return rect["x"] + rect["width"] // 2, rect["y"] + rect["height"] // 2


def _click_element(driver, element) -> None:
    try:
        element.click()
        return
    except Exception:
        rect = element.rect
        _tap_xy(driver, rect["x"] + rect["width"] // 2, rect["y"] + rect["height"] // 2)


def _click_xpath(driver, wait: WebDriverWait, xpath: str) -> None:
    element = wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, xpath)))
    _click_element(driver, element)


def _swipe_up(driver, duration_ms: int = 450, percent: float = 0.75) -> None:
    size = driver.get_window_size()
    center_x = size["width"] // 2
    start_y = int(size["height"] * 0.82)
    swipe_distance = max(int(size["height"] * percent * 0.45), 80)
    end_y = max(start_y - swipe_distance, int(size["height"] * 0.18))

    try:
        driver.execute_script(
            "mobile: swipeGesture",
            {
                "left": int(size["width"] * 0.15),
                "top": int(size["height"] * 0.20),
                "width": int(size["width"] * 0.70),
                "height": int(size["height"] * 0.60),
                "direction": "up",
                "percent": percent,
            },
        )
        return
    except Exception:
        pass

    driver.swipe(center_x, start_y, center_x, end_y, duration_ms)


def _point_in_rect(x: int, y: int, rect: dict, margin: int = 0) -> bool:
    return (
        rect["x"] - margin <= x <= rect["x"] + rect["width"] + margin
        and rect["y"] - margin <= y <= rect["y"] + rect["height"] + margin
    )


def _get_sticky_buttons_rect(driver):
    sticky_buttons = driver.find_elements(AppiumBy.ID, STICKY_BUTTONS_ID)
    if not sticky_buttons:
        return None
    return sticky_buttons[0].rect


def _is_element_blocked_by_sticky(driver, element, margin: int = 12) -> bool:
    sticky_rect = _get_sticky_buttons_rect(driver)
    if not sticky_rect:
        return False

    center_x, center_y = _element_center(element)
    return _point_in_rect(center_x, center_y, sticky_rect, margin=margin)


def _pair_titles_with_prices(driver, title_elements, price_elements):
    available_prices = list(price_elements)
    paired_items = []

    for title_element in title_elements:
        title_text = _element_text(title_element)
        if not title_text:
            continue

        title_x, title_y = _element_center(title_element)
        best_index = None
        best_score = None

        for idx, price_element in enumerate(available_prices):
            price_x, price_y = _element_center(price_element)
            delta_y = price_y - title_y
            delta_x = abs(price_x - title_x)

            if delta_y < 0 or delta_y > 220:
                continue
            if delta_x > 180:
                continue

            score = (delta_x, delta_y)
            if best_score is None or score < best_score:
                best_score = score
                best_index = idx

        matched_price = None
        blocked_by_sticky = False
        if best_index is not None:
            matched_price = available_prices.pop(best_index)
            blocked_by_sticky = _is_element_blocked_by_sticky(driver, matched_price)

        paired_items.append(
            {
                "title_element": title_element,
                "title_text": title_text,
                "price_element": matched_price,
                "blocked_by_sticky": blocked_by_sticky,
            }
        )

    return paired_items


def _find_elements_with_fallback(driver, resource_ids: tuple[str, ...]):
    for resource_id in resource_ids:
        elements = driver.find_elements(AppiumBy.ID, resource_id)
        if elements:
            return elements, resource_id
    return [], None


def _wait_for_elements_with_fallback(driver, resource_ids: tuple[str, ...], timeout_s: int):
    end_time = time.time() + timeout_s

    while time.time() < end_time:
        elements, resource_id = _find_elements_with_fallback(driver, resource_ids)
        if elements:
            return elements, resource_id
        time.sleep(0.5)

    raise TimeoutException(f"Expected elements were not found: {resource_ids}")


def _is_products_page_open(driver) -> bool:
    for resource_id in PRODUCT_LIST_READY_IDS:
        if driver.find_elements(AppiumBy.ID, resource_id):
            return True
    return False


def _create_driver(cfg: MarketplaceBotConfig):
    options = UiAutomator2Options().load_capabilities(
        {
            "platformName": cfg.platform_name,
            "deviceName": cfg.device_name,
            "appPackage": cfg.app_package,
            "automationName": cfg.automation_name,
            "noReset": cfg.no_reset,
        }
    )
    driver = webdriver.Remote(cfg.appium_url, options=options)
    wait = WebDriverWait(driver, cfg.wait_seconds)
    return driver, wait


def _go_to_products_page(driver, wait: WebDriverWait) -> None:
    logging.info("Opening the inventory tab...")
    wait.until(
        EC.element_to_be_clickable((AppiumBy.ID, BOTTOM_NAV_PRODUCTS_ID))
    ).click()

    time.sleep(1)
    if _is_products_page_open(driver):
        logging.info("Inventory list is already open.")
        return

    logging.info("Opening the items page...")
    try:
        products_tab = driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{PRODUCTS_TAB_TEXT}")'
        )
    except NoSuchElementException:
        products_tab = driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().textContains("{PRODUCTS_TAB_TEXT}")',
        )

    _click_element(driver, products_tab)
    _wait_for_elements_with_fallback(driver, PRODUCT_LIST_READY_IDS + PRODUCT_TITLE_IDS, 15)
    logging.info("Items list is open.")


def _close_filter_menu(driver, wait: WebDriverWait, sleep_after_s: float) -> None:
    logging.info("Opening the filter menu...")
    wait.until(
        EC.element_to_be_clickable((AppiumBy.ID, FILTER_BUTTON_ID))
    ).click()

    time.sleep(2)
    logging.info("Closing the filter menu with the back key...")
    _press_back(driver)
    time.sleep(sleep_after_s)


def _apply_sort_lowest_price(wait: WebDriverWait) -> None:
    logging.info("Opening the sort menu...")
    time.sleep(1)
    wait.until(
        EC.element_to_be_clickable((AppiumBy.ID, SORT_AREA_ID))
    ).click()

    time.sleep(2)
    try:
        wait.until(
            EC.element_to_be_clickable(
                (
                    AppiumBy.XPATH,
                    SORT_LOWEST_PRICE_XPATH,
                )
            )
        ).click()
        logging.info('"Lowest Price" option selected.')
    except TimeoutException:
        logging.error(
            '"Lowest Price" option was not found or could not be clicked. Keeping the default sort.'
        )

    time.sleep(1)


def _scroll_forward(driver) -> None:
    try:
        driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            "new UiScrollable(new UiSelector().scrollable(true)).scrollForward()",
        )
        return
    except WebDriverException as err:
        logging.warning("UiScrollable failed. Falling back to swipe: %s", err)

    _swipe_up(driver)


def _update_description_if_enabled(cfg: MarketplaceBotConfig, wait: WebDriverWait, driver) -> None:
    if not cfg.enable_description_update:
        return

    try:
        description_field = wait.until(
            EC.presence_of_element_located(
                (AppiumBy.ID, DESCRIPTION_INPUT_ID)
            )
        )

        current_description = description_field.text or description_field.get_attribute("text")
        if current_description and cfg.description_old_text in current_description:
            updated_description = current_description.replace(
                cfg.description_old_text, cfg.description_new_text
            )
            logging.info("Updating the description text...")
            description_field.clear()
            description_field.send_keys(updated_description)
        else:
            logging.info("Target description text not found. No changes applied.")
    except Exception as err:
        logging.warning(f"An error occurred while updating the description: {err}")


def run_marketplace_bot(cfg: MarketplaceBotConfig) -> None:
    setup_logging(cfg.log_file)

    driver, wait = _create_driver(cfg)
    logging.info("Driver started.")

    processed_titles: set[str] = set()
    scrolls_without_new_items = 0

    try:
        _go_to_products_page(driver, wait)

        if not cfg.enable_price_drop:
            _close_filter_menu(driver, wait, sleep_after_s=cfg.post_action_sleep_s)
            if cfg.enable_sort_lowest_price:
                _apply_sort_lowest_price(wait)

        logging.info("Inventory list is ready. Starting the loop...")

        while True:
            if scrolls_without_new_items >= cfg.max_scrolls_without_new_items:
                logging.warning(
                    "Reached the end of the list after %s attempts. Stopping.",
                    cfg.max_scrolls_without_new_items,
                )
                break

            try:
                visible_titles, title_resource_id = _wait_for_elements_with_fallback(
                    driver, PRODUCT_TITLE_IDS, cfg.wait_seconds
                )

                visible_prices = []
                visible_items = []
                if cfg.enable_price_drop:
                    visible_prices = driver.find_elements(AppiumBy.XPATH, EARNING_PRICE_XPATH)
                    visible_items = _pair_titles_with_prices(driver, visible_titles, visible_prices)

                logging.info(
                    "Visible items: %s titles (%s), %s price elements",
                    len(visible_titles),
                    title_resource_id,
                    len(visible_prices),
                )
            except TimeoutException:
                logging.warning("No item titles were found on the page. Stopping.")
                break

            found_new_product_on_this_screen = False
            retried_with_mini_scroll = False
            item_count = len(visible_titles)
            if cfg.enable_price_drop:
                item_count = len(visible_items)

            for i in range(item_count):
                try:
                    if cfg.enable_price_drop:
                        current_item = visible_items[i]
                        product_title_element = current_item["title_element"]
                        title_text = current_item["title_text"]
                        price_element = current_item["price_element"]
                        blocked_by_sticky = current_item["blocked_by_sticky"]
                    else:
                        product_title_element = visible_titles[i]
                        title_text = _element_text(product_title_element)
                        price_element = None
                        blocked_by_sticky = False

                    if not title_text or title_text in processed_titles:
                        continue

                    if cfg.enable_price_drop:
                        if price_element is None:
                            logging.warning("Price field could not be matched for '%s'. Skipping item.", title_text)
                            continue

                        if blocked_by_sticky:
                            logging.warning(
                                "Price field for '%s' overlaps with the sticky button area. Retrying after a small scroll.",
                                title_text,
                            )
                            _swipe_up(driver, duration_ms=220, percent=0.12)
                            time.sleep(1)
                            retried_with_mini_scroll = True
                            break

                        found_new_product_on_this_screen = True
                        scrolls_without_new_items = 0
                        logging.info("Updating price for: %s", title_text)
                        try:
                            _click_element(driver, price_element)
                            time.sleep(1)

                            price_input = wait.until(
                                EC.presence_of_element_located(
                                    (AppiumBy.ID, PRICE_INPUT_ID)
                                )
                            )

                            current_price_str = _element_text(price_input)
                            price_digits = ''.join(filter(str.isdigit, current_price_str))
                            if not price_digits:
                                raise ValueError(f"Could not parse the price value: {current_price_str!r}")

                            current_price = int(price_digits)
                            new_price = current_price - 1

                            price_input.clear()
                            price_input.send_keys(str(new_price))
                            logging.info(
                                "Current price: %s, new price entered: %s.",
                                current_price,
                                new_price,
                            )

                            _click_xpath(driver, wait, EARNING_PRICE_SUBMIT_XPATH)

                            time.sleep(cfg.post_action_sleep_s)
                            processed_titles.add(title_text)
                            logging.info("Price updated for '%s'.", title_text)
                            break
                        except Exception as e:
                            logging.error("An error occurred while updating the price: %s", e)
                            _press_back(driver)
                            time.sleep(1)
                            break
                    else:
                        found_new_product_on_this_screen = True
                        scrolls_without_new_items = 0
                        processed_titles.add(title_text)
                        logging.info("Opening item detail page: %s", title_text)
                        _click_element(driver, product_title_element)
                        time.sleep(2)

                        try:
                            _tap_xy(driver, cfg.edit_button_x, cfg.edit_button_y)
                            time.sleep(cfg.post_action_sleep_s)
                        except Exception as e:
                            logging.error("Could not click the edit button. Skipping item: %s", e)
                            _press_back(driver)
                            time.sleep(1)
                            _press_back(driver)
                            time.sleep(1)
                            continue

                        _update_description_if_enabled(cfg, wait, driver)

                        wait.until(
                            EC.element_to_be_clickable(
                                (AppiumBy.ID, APPROVAL_BUTTON_ID)
                            )
                        ).click()
                        logging.info('Clicked "Send for Approval".')

                        time.sleep(3)
                        _press_back(driver)
                        time.sleep(cfg.post_action_sleep_s)

                        if cfg.back_to_list_x is not None and cfg.back_to_list_y is not None:
                            _tap_xy(driver, cfg.back_to_list_x, cfg.back_to_list_y)
                            time.sleep(cfg.post_action_sleep_s)
                        else:
                            _press_back(driver)

                        _wait_for_elements_with_fallback(driver, PRODUCT_TITLE_IDS, cfg.wait_seconds)
                        time.sleep(1)
                        logging.info("Completed '%s' and returned to the list.", title_text)
                        break

                except StaleElementReferenceException:
                    logging.warning("Element became stale. Refreshing the list...")
                    break

            if retried_with_mini_scroll:
                logging.info("Re-scanning the screen after the small scroll...")
                continue

            if not found_new_product_on_this_screen:
                logging.info("All visible items are already processed. Scrolling down...")
                try:
                    _scroll_forward(driver)
                    scrolls_without_new_items += 1
                    time.sleep(2)
                except NoSuchElementException:
                    logging.warning("No scrollable area was found. End of list reached.")
                    break
                except WebDriverException as err:
                    logging.error("Appium connection was lost during scroll: %s", err)
                    break

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        logging.info("Process completed. The driver will close in 5 seconds.")
        time.sleep(5)
        driver.quit()
