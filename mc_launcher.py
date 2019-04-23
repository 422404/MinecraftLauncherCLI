#!/usr/bin/env python3

import os
import sys
import platform
import json
from argparse import ArgumentParser
from lib_mc_launcher import build_paths, construct_cmd, get_libs_manifests, get_main_class, download_manifest, download_assets_manifest, fetch_manifest, get_native_libs_manifests
from lib_mc_download import download_assets, download_client, download_libs

def get_base_config():
    return {"__comment": "Minecraft Launcher CLI config"}


def write_config(game_dir: str, config: dict) -> bool:
    config_file_path = os.path.join(game_dir, "mc_launcher.json")
    try:
        with open(config_file_path, "w") as config_file:
            config_file.write(json.dumps(config))
    except:
        return True
    
    return False


def read_config(game_dir: str) -> dict:
    config_file_path = os.path.join(game_dir, "mc_launcher.json")
    try:
        with open(config_file_path, "r") as config_file:
            return json.load(config_file)
    except:
        return None


def launch(game_dir: str, verbose: bool, username: str, fullscreen: bool, show_cmd: str):
    config = read_config(game_dir)
    if config == None:
        print("No config found, please download a minecraft version first.")
        exit(1)
    
    if not "version" in config:
        print("No current version, please switch to or download one first.")
        exit(1)
    
    paths = build_paths(game_dir)
    version = config["version"]
    version_dir   = os.path.join(paths["versions_dir"], version)
    client_path   = os.path.join(version_dir, "{}.jar".format(version))
    manifest_path = os.path.join(version_dir, "{}.json".format(version))
    manifest = None
    try:
        with open(manifest_path, "r") as manifest_file:
            manifest = json.load(manifest_file)
    except:
        print("Error while opening manifest.")
        exit(1)
    
    libs_manifests = get_libs_manifests(manifest)
    libs_file_paths = [ os.path.join(paths["libs_dir"], lib["path"]) for lib in libs_manifests]
    is_windows = platform.system() == "Windows"
    sep = ";" if is_windows else ":"
    platforms = {"Windows": "windows", "Linux": "linux", "Darwin": "osx"}
    natives_manifests, err = get_native_libs_manifests(platforms[platform.system()], manifest)
    if err:
        print("Error while reading native libs manifests.")
        exit(1)
    natives_file_paths = [ os.path.join(paths["natives_dir"], lib["path"]) for lib in natives_manifests]
    classpath = sep.join(libs_file_paths) + sep + sep.join(natives_file_paths)

    # TODO take care of authentication
    command = construct_cmd(is_windows, client_path, get_main_class(manifest), classpath, username, version, game_dir,
            paths["assets_dir"], manifest["assets"], "0", "0", "mojang", manifest["type"], fullscreen)
    
    if show_cmd:
        print(("Command: " if verbose else "") + command)
        return
    
    exit_code = os.system(command)
    if exit_code:
        print("Error launching the game, error code:", exit_code)
        exit(1) 


def switch_version(version: str, download: bool, game_dir: str, verbose: bool):
    version_manifest_file_path = os.path.join(game_dir, "versions", version, "{}.json".format(version))
    if not os.path.exists(version_manifest_file_path):
        print("{} manifest not found locally.".format(version))
        if download:
            print("Downloading {} files from servers.".format(version))
            download_version(version, game_dir, verbose)

    config = read_config(game_dir)
    if config == None:
        if verbose:
            print("No mc_launcher.json config found, one has been generated.")
        config = get_base_config()
    
    config["version"] = version
    write_config(game_dir, config)


def download_version(version: str, game_dir: str, verbose: bool):
    manifest, err = download_manifest()
    if err:
        print("Failed to download minecraft manifest.")
        exit(1)
    
    if version == "latest":
        version = manifest["latest"]["release"]
    
    found = False
    version_info = None
    for v in manifest["versions"]:
        if v["id"] == version:
            found = True
            version_info = v
            break
    if not found:
        print("Version", version, "does not exist.")
        exit(1)
    
    version_manifest, err = fetch_manifest(version_info["url"])
    if err:
        print("Failed to download version", version, "manifest.")
        exit(1)
    
    assets_manifest, err = download_assets_manifest(version_manifest)
    if err:
        print("Failed to download assets manifest.")
        exit(1)
    
    paths = build_paths(game_dir)
    err = download_assets(paths["assets_dir"], assets_manifest, version_manifest["assets"], verbose)
    if err:
        print("Error while downloading assets.")
        exit(1)
    
    err = download_client(paths["versions_dir"], version_manifest, version, verbose)
    if err:
        print("Error while downloading client executable.")
        exit(1)
    
    libs = get_libs_manifests(version_manifest)
    err = download_libs(paths["libs_dir"], libs, verbose)
    if err:
        print("Error while downloading libs.")
        exit(1)
    
    platforms = {"Windows": "windows", "Linux": "linux", "Darwin": "osx"}
    natives, err = get_native_libs_manifests(platforms[platform.system()], version_manifest)
    if err:
        print("Unsupported system.")
        exit(1)
    
    err = download_libs(paths["natives_dir"], natives, verbose)
    if err:
        print("Error while downloading native libs.")
        exit(1)
    
    config = read_config(game_dir)
    if config == None:
        if verbose:
            print("No mc_launcher.json config found, one has been generated.")
        config = get_base_config()
        config["version"] = version
        write_config(game_dir, config)


def main():
    parser = ArgumentParser()
    parser.add_argument("-d", "--game-dir", metavar="PATH", dest="game_dir", type=str, default="~/.minecraft",
            help="game directory, defaults to %(default)s")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="verbose output")

    base_subparsers = parser.add_subparsers(title="Subcommands", dest="base_cmd")
    launch_parser: ArgumentParser = base_subparsers.add_parser("launch", help="launch the game",
            description="Launch the game.")
    version_parser: ArgumentParser = base_subparsers.add_parser("version", help="game versions utils",
            description="Game versions utils.")
    
    launch_parser.add_argument("username", type=str, help="Player name")
    launch_parser.add_argument("--fullscreen", dest="fullscreen", action="store_true", help="launch game in fullscreen mode")
    launch_parser.add_argument("--show-cmd", dest="show_cmd", action="store_true", help="don't launch the game, only prints the launching cmd")

    version_subparsers = version_parser.add_subparsers(title="Subcommands", dest="version_cmd")
    version_switch_parser: ArgumentParser = version_subparsers.add_parser("switch", help="switch version",
            description="Switch currently used game version.")
    version_download_parser: ArgumentParser = version_subparsers.add_parser("download", help="download game version",
            description="Download some minecraft version.")

    version_switch_parser.add_argument("version", type=str, help="Game version to switch to")
    version_switch_parser.add_argument("--download", dest="download", action="store_true",
            help="download version files if not present")
    version_download_parser.add_argument("version", type=str, help="Game version to download")

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = vars(parser.parse_args())
        if args["base_cmd"] == "version" and args["version_cmd"] == None:
            version_parser.print_help()

        elif args["base_cmd"] == "launch":
            launch(args["game_dir"], args["verbose"], args["username"], args["fullscreen"], args["show_cmd"])

        elif args["base_cmd"] == "version" and args["version_cmd"] == "switch":
            switch_version(args["version"], args["download"], args["game_dir"], args["verbose"])

        elif args["base_cmd"] == "version" and args["version_cmd"] == "download":
            download_version(args["version"], args["game_dir"], args["verbose"])
        
        else:
            print("Unexpected error")
            exit(1)


if __name__ == "__main__":
    main()
