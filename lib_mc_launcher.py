import os
import json
import requests
from typing import List

MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
ASSETS_URL   = "https://resources.download.minecraft.net/{}/{}"

def fetch_manifest(url: str) -> (dict, bool):
    req = requests.get(url)
    return (req.json() if req.ok else None, not req.ok)

# Downloads the versions manifest
# Returns (json, err)
def download_manifest() -> (dict, bool):
    return fetch_manifest(MANIFEST_URL)

# Gets native libs manifests
# platform: linux | osx | windows
# Returns (native libs manifest, err)
def get_native_libs_manifests(platform: str, version_manifest: dict) -> (List[dict], bool):
    if platform in ["linux", "osx", "windows"]:
        natives = [lib["downloads"]["classifiers"][lib["natives"][platform]]
                   for lib in version_manifest["libraries"]
                   if "natives" in lib and platform in lib["natives"]]
        return (natives, False)
    else:
        return (None, True)

# Gets libs manifests
# Returns (libs manifests, err)
def get_libs_manifests(version_manifest: dict) -> List[dict]:
    libs = [lib["downloads"]["artifact"] for lib in version_manifest["libraries"]]
    return libs

# Gets client manifest
# Returns (client manifest, err)
def get_client_manifest(version_manifest: dict) -> dict:
    return version_manifest["downloads"]["client"]

# Checks if the version is a release
def is_release(version_manifest: dict) -> bool:
    return version_manifest["type"] == "release"

# Gets main class of minecraft.jar
def get_main_class(version_manifest: dict) -> str:
    return version_manifest["mainClass"]

# Downloads the assets manifest
# Returns (assets manifest, err)
def download_assets_manifest(version_manifest: dict) -> (dict, bool):
    return fetch_manifest(version_manifest["assetIndex"]["url"])

# Gets asset url
def get_asset_url(asset_hash: str) -> str:
    return ASSETS_URL.format(asset_hash[:2], asset_hash)

# Get asset path
def get_asset_path(asset_hash: str) -> str:
    return os.path.join(asset_hash[:2], asset_hash)

# Constructs launch cmd
def construct_cmd(is_windows: bool, client_jar: str, main_class: str,
                  classpath: str, username: str, version: str,
                  game_dir: str, assets_dir: str, assets_index: str,
                  access_token: str, uuid: str, user_type: str,
                  version_type: str, fullscreen: bool) -> str:
    option_fullscreen = "--fullscreen" if fullscreen else ""
    sep = ";" if is_windows else ":"
    java_cmd = "javaw" if is_windows else "java"
    client_args = "--username {} --version {} --gameDir {} --assetsDir {} --assetIndex {} --accessToken {} --uuid {} --userType {} --versionType {} {fullscreen}" \
                  .format(username, version, game_dir, assets_dir, assets_index, access_token, uuid, user_type, version_type, fullscreen=option_fullscreen)
    jvm_args = "-cp {}{}{} {}".format(classpath, sep, client_jar, main_class)
    return "{} {} {}".format(java_cmd, jvm_args, client_args)

# Builds all the paths from the game dir
def build_paths(game_dir: str) -> dict:
    return {
        "assets_dir": os.path.join(game_dir, "assets"),
        "libs_dir": os.path.join(game_dir, "libraries"),
        "natives_dir": os.path.join(game_dir, "natives"),
        "versions_dir": os.path.join(game_dir, "versions")
    }
