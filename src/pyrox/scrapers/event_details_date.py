"""
Scrape date information from an event detail page.
"""

import json
import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser

from .base import BaseScraper


class DateParser:
    """
    A class for parsing dates from strings.
    Supports multiple date formats with fallback strategies.
    """

    # Common date format patterns
    DATE_FORMATS = [
        "%Y-%m-%d",  # ISO format: 2018-10-20
        "%b %d, %Y",  # Oct 20, 2018
        "%B %d, %Y",  # October 20, 2018
        "%d %b %Y",  # 20 Oct 2018
        "%d %B %Y",  # 20 October 2018
        "%Y-%m-%dT%H:%M:%S",  # ISO with time: 2018-10-20T00:00:00
        "%Y-%m-%dT%H:%M:%SZ",  # ISO with time and Z: 2018-10-20T00:00:00Z
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO with microseconds
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO with microseconds and Z
    ]

    def __init__(self) -> None:
        pass

    def parse(self, text: str, year: int | None = None) -> datetime:
        """
        Parse a datetime from the provided text.
        Tries multiple parsing strategies in order until one succeeds.
        :param text: The text containing the date
        :param year: Optional year to use if not present in the date string
        :return: The parsed datetime
        :raises: ValueError on failure to parse
        """
        if not text or not text.strip():
            raise ValueError("empty or whitespace-only date string")

        text = text.strip()

        # Try parsing month-day ranges (e.g., "Mar 2-3") - requires year
        if year is not None:
            try:
                return self._try_parse_month_day_range(text, year)
            except ValueError:
                pass

            # Also try parsing just month-day format (e.g., "Mar 2") when year is provided
            try:
                return self._try_parse_month_day(text, year)
            except ValueError:
                pass

        # Try explicit format patterns first
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        # Try parsing ISO date ranges (e.g., "2018-10-20/2018-10-21")
        try:
            return self._try_parse_iso_range(text)
        except ValueError:
            pass

        # Try dateutil parser as a fallback (handles many formats)
        # But only if year wasn't provided, or if the text contains a year
        if year is None or self._text_contains_year(text):
            try:
                parsed = dateutil_parser.parse(text, fuzzy=False)
                return parsed
            except (ValueError, TypeError):
                pass

            # Try fuzzy parsing with dateutil (more lenient)
            try:
                parsed = dateutil_parser.parse(text, fuzzy=True)
                return parsed
            except (ValueError, TypeError):
                pass
        else:
            # Year was provided but text doesn't contain a year
            # Don't use dateutil parser here as it may use wrong defaults
            # The month-day parsing should have caught this already
            pass

        raise ValueError(f"unable to parse date from: {text}")

    def _try_parse_iso_range(self, text: str) -> datetime:
        """
        Try to parse an ISO date range and return the start date.
        :param text: The text containing the date range
        :return: The parsed datetime (start date)
        :raises: ValueError if not a valid ISO range
        """
        # Look for patterns like "2018-10-20/2018-10-21" or "2018-10-20 - 2018-10-21"
        range_patterns = [
            r"(\d{4}-\d{2}-\d{2})[/-](\d{4}-\d{2}-\d{2})",  # ISO range with / or -
            r"(\d{4}-\d{2}-\d{2})\s+-\s+(\d{4}-\d{2}-\d{2})",  # ISO range with space and dash
        ]

        for pattern in range_patterns:
            match = re.search(pattern, text)
            if match:
                start_date_str = match.group(1)
                return datetime.strptime(start_date_str, "%Y-%m-%d")

        raise ValueError("not an ISO date range format")

    def _text_contains_year(self, text: str) -> bool:
        """
        Check if the text contains a 4-digit year.
        :param text: The text to check
        :return: True if text contains a year, False otherwise
        """
        return bool(re.search(r"\b(19|20)\d{2}\b", text))

    def _try_parse_month_day_range(self, text: str, year: int) -> datetime:
        """
        Try to parse a month-day range (e.g., "Mar 2-3") and return the start date.
        :param text: The text containing the date range (e.g., "Mar 2-3")
        :param year: The year to use for the date
        :return: The parsed datetime (start date)
        :raises: ValueError if not a valid month-day range
        """
        # Patterns for month-day ranges:
        # "Mar 2-3" -> March 2
        # "Mar 2 - 3" -> March 2
        # "March 2-3" -> March 2
        range_patterns = [
            r"([A-Za-z]+)\s+(\d+)\s*-\s*(\d+)",  # "Mar 2-3" or "Mar 2 - 3"
        ]

        for pattern in range_patterns:
            match = re.search(pattern, text)
            if match:
                month_str = match.group(1)
                start_day = int(match.group(2))

                # Try to parse the month
                try:
                    # Try abbreviated month first
                    month_date = datetime.strptime(f"{month_str} {start_day}", "%b %d")
                    return month_date.replace(year=year)
                except ValueError:
                    try:
                        # Try full month name
                        month_date = datetime.strptime(
                            f"{month_str} {start_day}", "%B %d"
                        )
                        return month_date.replace(year=year)
                    except ValueError:
                        continue

        raise ValueError("not a valid month-day range format")

    def _try_parse_month_day(self, text: str, year: int) -> datetime:
        """
        Try to parse a month-day format (e.g., "Mar 2") and return the date.
        :param text: The text containing the date (e.g., "Mar 2")
        :param year: The year to use for the date
        :return: The parsed datetime
        :raises: ValueError if not a valid month-day format
        """
        # Patterns for month-day:
        # "Mar 2" -> March 2
        # "March 2" -> March 2
        patterns = [
            r"([A-Za-z]+)\s+(\d+)",  # "Mar 2" or "March 2"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                month_str = match.group(1)
                day = int(match.group(2))

                # Try to parse the month
                try:
                    # Try abbreviated month first
                    month_date = datetime.strptime(f"{month_str} {day}", "%b %d")
                    return month_date.replace(year=year)
                except ValueError:
                    try:
                        # Try full month name
                        month_date = datetime.strptime(f"{month_str} {day}", "%B %d")
                        return month_date.replace(year=year)
                    except ValueError:
                        continue

        raise ValueError("not a valid month-day format")


class EventDetailsDateScraper(BaseScraper):
    """
    A class for scraping dates from event detail pages.
    Supports multiple page formats with fallback strategies.
    """

    def __init__(self, logger: logging.Logger) -> None:
        super().__init__(logger)
        self.date_parser = DateParser()

    def scrape(self, soup: BeautifulSoup) -> datetime:
        """
        Scrape and parse the event date from the page.
        Tries multiple extraction strategies in order until one succeeds.
        :param soup: The parsed page markup
        :return: The date of the event
        :raises: RuntimeError if all strategies fail
        """
        # Try each extraction strategy in order
        strategies = [
            self._extract_from_text_gray_300_div_with_title_year,
            self._extract_from_text_gray_300_div,
            self._extract_from_json_ld,
        ]

        for strategy in strategies:
            try:
                date = strategy(soup)
                if date is not None:
                    return date
            except Exception as e:
                self.logger.debug(f"Date extraction strategy failed: {e}")
                continue

        raise RuntimeError("failed to parse date from event details page")

    def _extract_from_text_gray_300_div_with_title_year(
        self, soup: BeautifulSoup
    ) -> datetime | None:
        """
        Extract date from a div with text-gray-300 class, using year from title.
        This handles the second page type format where date is "Mar 2-3" and year is in title.
        :param soup: The parsed page markup
        :return: The parsed date, or None if not found
        """
        # First, try to extract the year from the title (h1 tag)
        year = self._extract_year_from_title(soup)
        if year is None:
            return None

        # Look for divs with the text-gray-300 class
        divs = soup.find_all("div", class_="text-gray-300")
        for div in divs:
            text = div.get_text(strip=True)
            if not text:
                continue
            try:
                # Try parsing with the year from title
                return self.date_parser.parse(text, year=year)
            except ValueError:
                continue
        return None

    def _extract_year_from_title(self, soup: BeautifulSoup) -> int | None:
        """
        Extract the year from the event title (h1 tag).
        :param soup: The parsed page markup
        :return: The year, or None if not found
        """
        h1 = soup.find("h1")
        if h1 is None:
            return None

        # Get all text from h1, including nested elements
        title_text = h1.get_text(separator=" ", strip=True)
        # Look for 4-digit year in the title (e.g., "HYROX Glasgow 2024")
        year_match = re.search(r"\b(19|20)\d{2}\b", title_text)
        if year_match:
            year = int(year_match.group(0))
            # Sanity check: year should be reasonable (between 1900 and 2100)
            if 1900 <= year <= 2100:
                return year
        return None

    def _extract_from_text_gray_300_div(self, soup: BeautifulSoup) -> datetime | None:
        """
        Extract date from a div with text-gray-300 class.
        This is the first page type format.
        :param soup: The parsed page markup
        :return: The parsed date, or None if not found
        """
        # Look for divs with the text-gray-300 class
        # The date appears in a div with classes: "flex flex-row gap-2 items-center font-bold text-sm md:text-base text-gray-300"
        divs = soup.find_all("div", class_="text-gray-300")
        for div in divs:
            text = div.get_text(strip=True)
            if not text:
                continue

            # Check if text contains a year
            text_has_year = self.date_parser._text_contains_year(text)

            try:
                parsed = self.date_parser.parse(text)
                # If text doesn't contain a year but we got a date, check if it's a suspicious default year
                # dateutil parser might default to 2003 when it can't determine the year
                if not text_has_year:
                    # 2003 is a known default year used by dateutil parser
                    if parsed.year == 2003:
                        year = self._extract_year_from_title(soup)
                        if year is not None:
                            try:
                                return self.date_parser.parse(text, year=year)
                            except ValueError:
                                pass
                return parsed
            except ValueError:
                # If parsing failed and text doesn't contain a year, try extracting year from title
                if not text_has_year:
                    year = self._extract_year_from_title(soup)
                    if year is not None:
                        try:
                            return self.date_parser.parse(text, year=year)
                        except ValueError:
                            continue
                continue
        return None

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> datetime | None:
        """
        Extract date from JSON-LD structured data.
        :param soup: The parsed page markup
        :return: The parsed date, or None if not found
        """
        # Look for script tags with type="application/ld+json"
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)  # type: ignore
                if isinstance(data, dict) and "startDate" in data:
                    start_date_str = data["startDate"]
                    # Parse ISO format date (e.g., "2018-10-20")
                    return self.date_parser.parse(start_date_str)
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
        return None
