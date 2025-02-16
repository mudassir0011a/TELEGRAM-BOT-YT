import json

def convert_to_netscape(json_file, output_file):
    with open(json_file, 'r') as f:
        cookies = json.load(f)

    with open(output_file, 'w') as f:
        for cookie in cookies:
            f.write(
                f"{cookie['domain']}\t"
                f"{'TRUE' if cookie['hostOnly'] else 'FALSE'}\t"
                f"{cookie['path']}\t"
                f"{'TRUE' if cookie['secure'] else 'FALSE'}\t"
                f"{int(cookie['expirationDate'])}\t"
                f"{cookie['name']}\t"
                f"{cookie['value']}\n"
            )

convert_to_netscape('cookies.txt', 'cookies_netscape.txt')