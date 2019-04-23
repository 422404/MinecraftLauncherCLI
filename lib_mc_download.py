import os
import json
import requests
import shutil
from typing import List
from lib_mc_launcher import get_asset_path, get_asset_url, get_client_manifest

# Downloads assets manifest and assets files
# Returns True if error
def download_assets(assets_dir: str, assets_manifest: dict, assets_index: str, verbose: bool) -> bool:
    assets_index_dir = os.path.join(assets_dir, "indexes")
    assets_objects_dir = os.path.join(assets_dir, "objects")
    try:
        os.makedirs(assets_index_dir, exist_ok=True)
        os.makedirs(assets_objects_dir, exist_ok=True)
    except:
        if verbose:
            print("Error while creating directory structure.\n")
        return True

    assets_index_file_path = os.path.join(assets_index_dir, "{}.json".format(assets_index))
    if verbose:
        print("Writing assets manifest to", assets_index_file_path)
    with open(assets_index_file_path, "w") as assets_manifest_file:
        assets_manifest_file.write(json.dumps(assets_manifest))

    for asset_key in assets_manifest["objects"]:
        asset_hash = assets_manifest["objects"][asset_key]["hash"]
        asset_file_path = os.path.join(assets_objects_dir, get_asset_path(asset_hash))
        url = get_asset_url(asset_hash)
        # don't re-download content
        if os.path.exists(asset_file_path):
            if verbose:
                print("Already downloaded:", url)
            continue

        if verbose:
            print("Downloading:", url)
        req = requests.get(url, stream=True)
        if not req.ok:
            if verbose:
                print("Asset download failed, url =", url)
                return True
        else:
            asset_dir_path = os.path.dirname(asset_file_path)
            if not os.path.exists(asset_dir_path):
                os.mkdir(asset_dir_path)
            
            try:
                with open(asset_file_path, "wb") as asset_file:
                    req.raw.decode_content = True
                    shutil.copyfileobj(req.raw, asset_file)
            except:
                if verbose:
                    print("Error while writing file:", asset_file_path)
                    return True
    return False


# Downloads client executable
# Returns True if error
def download_client(versions_dir: str, version_manifest: dict, version: str, verbose: bool) -> bool:
    version_dir = os.path.join(versions_dir, version)
    try:
        os.makedirs(version_dir, exist_ok=True)
    except:
        if verbose:
            print("Failed to creating file structure.")
            return True
    
    client_manifest = get_client_manifest(version_manifest)
    url = client_manifest["url"]
    client_file_path = os.path.join(version_dir, "{}.jar".format(version))
    if os.path.exists(client_file_path):
        if verbose:
            print("Client executable already downloaded.")
    else:
        if verbose:
            print("Downloading:", url)
        
        req = requests.get(url, stream=True)
        try:
            with open(client_file_path, "wb") as client_file:
                req.raw.decode_content = True
                shutil.copyfileobj(req.raw, client_file)
        except:
            if verbose:
                print("Error while writting client executable file:", client_file_path)
                return True
    
    version_manifest_file_path = os.path.join(version_dir, "{}.json".format(version))
    with open(version_manifest_file_path, "w") as version_manifest_file:
        version_manifest_file.write(json.dumps(version_manifest))
    return False


# Downloads libraries (natives or not)
# Return True if error
def download_libs(out_dir: str, libs: List[dict], verbose: bool) -> bool:
    for lib in libs:
        url = lib["url"]
        lib_file_path = os.path.join(out_dir, lib["path"])
        if os.path.exists(lib_file_path):
            if verbose:
                print("Already downloaded:", url)
            continue

        if verbose:
            print("Downloading:", url)
        
        try:
            os.makedirs(os.path.dirname(lib_file_path), exist_ok=True)
        except:
            if verbose:
                print("Failed to create directory structure.")
            return True
        
        req = requests.get(url, stream=True)
        try:
            with open(lib_file_path, "wb") as lib_file:
                req.raw.decode_content = True
                shutil.copyfileobj(req.raw, lib_file)
        except:
            if verbose:
                print("Error while writting lib file:", lib_file_path)
            return True

    return False
