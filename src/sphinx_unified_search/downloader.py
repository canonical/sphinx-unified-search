import requests
from sphinx.util import logging

logger = logging.getLogger(__name__)


def download_searchindex(url: str) -> str:
    logger.info(
        "[unified-search] downloading %s",
        url,
    )

    try:
        response = requests.get(url, timeout=30)

        logger.info(
            "[unified-search] response status: %s",
            response.status_code,
        )

        response.raise_for_status()

        logger.info(
            "[unified-search] downloaded %d bytes",
            len(response.text),
        )

        return response.text

    except Exception as exc:
        logger.warning(
            "[unified-search] failed to download %s: %s",
            url,
            exc,
        )
        raise