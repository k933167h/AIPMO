"""Read-only discovery of Zulip topics and Nextcloud WebDAV resources."""
import os
import xml.etree.ElementTree as ET
from urllib.parse import quote
from urllib.request import Request,build_opener
from app.collaboration import _base,_basic,_json_get,_NoRedirect

def zulip_recent_messages(stream_id,limit=100):
    if not isinstance(stream_id,int) or stream_id<=0 or not 1<=limit<=100:
        raise ValueError("invalid Zulip request")
    base=_base(os.getenv("PMO_ZULIP_URL"))
    headers={"Authorization":_basic(os.getenv("PMO_ZULIP_EMAIL"),os.getenv("PMO_ZULIP_API_KEY"))}
    path="/api/v1/messages?anchor=newest&num_before="+str(limit)+"&num_after=0"
    result=_json_get(base,path,headers)
    if result.get("result")!="success": raise ValueError("invalid Zulip response")
    return [m for m in result.get("messages",[]) if m.get("stream_id")==stream_id]

def nextcloud_list_folder(folder=""):
    if ".." in folder.split("/") or folder.startswith("/"): raise ValueError("invalid folder")
    base=_base(os.getenv("PMO_NEXTCLOUD_URL"))
    user=os.getenv("PMO_NEXTCLOUD_USER")
    auth=_basic(user,os.getenv("PMO_NEXTCLOUD_APP_PASSWORD"))
    path="/remote.php/dav/files/"+quote(user,safe="")+"/"+quote(folder,safe="/")
    req=Request(base+path,headers={"Authorization":auth,"Depth":"1"},method="PROPFIND")
    with build_opener(_NoRedirect).open(req,timeout=10) as response:
        payload=response.read(1048576)
    root=ET.fromstring(payload)
    ns={"d":"DAV:"}
    results=[]
    for item in root.findall("d:response",ns):
        href=item.findtext("d:href",default="",namespaces=ns)
        if href: results.append({"href":href})
    return results
