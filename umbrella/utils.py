from urllib.parse import urlparse, ParseResult, urlunparse, urlsplit, SplitResult
import typing
import datetime
import platform


def url_hide_sensitive(original_url: typing.AnyStr) -> str:
    """
    Hide the username and password fragments in a URL to prevent sensitive information appearing in the log.
    :param original_url: The original URL
    :return: The transformed URL
    """
    u: ParseResult = urlparse(original_url)
    u2 = list(u)

    # note: the doc (https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse) is fake, you can't
    # really edit a ParseResult or SplitResult
    # also don't use u.geturl()
    if u.netloc and "@" in u.netloc:
        s = u.netloc.split("@", maxsplit=1)
        s[0] = "***"
        print(s)
        u2[1] = '@'.join(s)

    return urlunparse(u2)


def get_timestamp() -> int:
    """
    Get current UNIX timestamp in UTC.
    :return: timestamp
    """
    # https://stackoverflow.com/a/22101249/2646069
    d = datetime.datetime.utcnow()
    epoch = datetime.datetime(1970, 1, 1)
    return (d - epoch).total_seconds()


def get_os_string() -> str:
    return platform.platform()