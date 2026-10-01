"""Thin wrapper around the Instagram Graph API endpoints we use.

Docs: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api
"""
import os
import time

import requests

GRAPH_VERSION = os.environ.get("GRAPH_API_VERSION", "v21.0")
BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"


class GraphAPIError(RuntimeError):
    pass


def _check(resp: requests.Response) -> dict:
    data = resp.json()
    if resp.status_code >= 400 or "error" in data:
        raise GraphAPIError(f"Graph API error {resp.status_code}: {data}")
    return data


def create_media_container(ig_user_id: str, image_url: str, caption: str, token: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/{ig_user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=30,
    )
    return _check(resp)["id"]


def create_reels_container(ig_user_id: str, video_url: str, caption: str, token: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token,
        },
        timeout=30,
    )
    return _check(resp)["id"]


def wait_until_container_ready(container_id: str, token: str, timeout_s: int = 120) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = requests.get(
            f"{BASE_URL}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        status = _check(resp).get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise GraphAPIError(f"Media container {container_id} failed processing")
        time.sleep(5)
    raise GraphAPIError(f"Media container {container_id} did not finish processing in time")


def publish_media(ig_user_id: str, container_id: str, token: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    return _check(resp)["id"]


def get_account_username(ig_user_id: str, token: str) -> str:
    resp = requests.get(
        f"{BASE_URL}/{ig_user_id}",
        params={"fields": "username", "access_token": token},
        timeout=30,
    )
    return _check(resp).get("username", "")


def get_recent_media(ig_user_id: str, token: str, limit: int = 20) -> list:
    resp = requests.get(
        f"{BASE_URL}/{ig_user_id}/media",
        params={"fields": "id,timestamp,permalink", "limit": limit, "access_token": token},
        timeout=30,
    )
    return _check(resp).get("data", [])


def get_comments(media_id: str, token: str) -> list:
    resp = requests.get(
        f"{BASE_URL}/{media_id}/comments",
        params={"fields": "id,text,username,timestamp", "access_token": token},
        timeout=30,
    )
    return _check(resp).get("data", [])


def reply_to_comment(comment_id: str, message: str, token: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/{comment_id}/replies",
        data={"message": message, "access_token": token},
        timeout=30,
    )
    return _check(resp)["id"]
