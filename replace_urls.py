import re
import os
import sys
import yaml
import requests

# ===== 设置部分 =====
ST_FILE = "collapsed-tiles/collapsed-tiles-example.stoverride"  # 主 YAML 文件
GEMINI_JS = "collapsed-tiles/script/Gemini.js"  # 新 JS 文件名 (大写 G)
GEMINI_URL = "https://gemini.google.com"  # Gemini 检测 URL
GEMINI_TITLE = "Gemini"  # Gemini tile 标题
GEMINI_ICON = "https://cdn.jsdmirror.com/gh/xiyingruyi/misc@main/collapsed-tiles/img/gemini-color.png"  # Gemini 图标 CDN
GEMINI_JS_URL = "https://cdn.jsdmirror.com/gh/xiyingruyi/misc@main/collapsed-tiles/script/Gemini.js"  # 新 provider URL (大写 G)
UPSTREAM_ST_RAW = "https://raw.githubusercontent.com/StashNetworks/misc/main/collapsed-tiles/collapsed-tiles-example.stoverride"  # 上游 YAML raw
UPSTREAM_JS_RAW = "https://raw.githubusercontent.com/StashNetworks/misc/main/collapsed-tiles/script/chatgpt-app.js"  # 上游 JS raw (源)

# ===== 辅助函数: 域名替换 =====
def replace_domain(url):
    """替换 fastly.jsdelivr.net 为 cdn.jsdmirror.com (精确 gh 路径)"""
    return re.sub(r'(https://fastly\.jsdelivr\.net)(/gh[^"\s]+)', r'https://cdn.jsdmirror.com\2', url)

# ===== 辅助函数: 下载初始文件 =====
def download_initial_file(file_path, upstream_raw, fallback_content):
    """如果文件不存在，从上游 raw 下载初始 (fallback 到模板)"""
    try:
        response = requests.get(upstream_raw, timeout=10)
        if response.status_code == 200:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"📥 已从上游下载初始 {file_path}")
            return True
    except Exception as e:
        print(f"⚠️ 下载上游失败: {e}，使用 fallback 模板")

    # Fallback 到初始模板
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(fallback_content)
    print(f"📥 已使用 fallback 模板创建 {file_path}")
    return True

# ===== 1. 修改 collapsed-tiles/collapsed-tiles-example.stoverride =====
if not os.path.exists(ST_FILE):
    initial_yaml = """name: Collapsed Tiles Example

tiles:
  - name: ChatGPT-Web-Check
    title: ChatGPT Web
    icon: https://fastly.jsdelivr.net/gh/StashNetworks/misc@main/collapsed-tiles/img/chatgpt.png
    collapsed: true
    url: https://chatgpt.com
  - name: ChatGPT-App-Check
    title: ChatGPT App
    icon: https://fastly.jsdelivr.net/gh/StashNetworks/misc@main/collapsed-tiles/img/chatgpt.png
    collapsed: true
    url: https://chatgpt.com
  - name: YouTube-Check
    title: YouTube
    icon: https://fastly.jsdelivr.net/gh/StashNetworks/misc@main/collapsed-tiles/img/youtube.png
    collapsed: true
    url: https://www.youtube.com
  - name: Netflix-Check
    title: Netflix
    icon: https://fastly.jsdelivr.net/gh/StashNetworks/misc@main/collapsed-tiles/img/netflix.png
    collapsed: true
    url: https://www.netflix.com

script-providers:
  ChatGPT-Web-Check:
    url: https://fastly.jsdelivr.net/gh/StashNetworks/misc@main/collapsed-tiles/script/chatgpt-web.js
  ChatGPT-App-Check:
    url: https://fastly.jsdelivr.net/gh/StashNetworks/misc@main/collapsed-tiles/script/chatgpt-app.js
  YouTube-Check:
    url: https://fastly.jsdelivr.net/gh/StashNetworks/misc@main/collapsed-tiles/script/youtube.js
  Netflix-Check:
    url: https://fastly.jsdelivr.net/gh/StashNetworks/misc@main/collapsed-tiles/script/netflix.js
"""
    download_initial_file(ST_FILE, UPSTREAM_ST_RAW, initial_yaml)

if os.path.exists(ST_FILE):
    with open(ST_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    try:
        data = yaml.safe_load(content)
        changed = False

        # 步骤 1: 域名替换所有 URL
        for tile in data.get('tiles', []):
            if 'icon' in tile:
                tile['icon'] = replace_domain(tile['icon'])
                changed = True
            if 'url' in tile:
                tile['url'] = replace_domain(tile['url'])
                changed = True

        for provider_name, provider in data.get('script-providers', {}).items():
            if 'url' in provider:
                provider['url'] = replace_domain(provider['url'])
                changed = True

        print(f"🔧 域名替换完成: {len(data.get('tiles', []))} 个 tiles, {len(data.get('script-providers', {}))} 个 providers")

        # 步骤 2: 改 ChatGPT-App-Check tile
        for tile in data.get('tiles', []):
            if tile.get('name') == 'ChatGPT-App-Check':
                tile['name'] = 'Gemini-Check'
                tile['title'] = GEMINI_TITLE
                tile['icon'] = GEMINI_ICON
                tile['url'] = GEMINI_URL
                changed = True
                print("🔧 Tile 替换完成: ChatGPT-App-Check → Gemini-Check")

        # 步骤 3: 改 script-providers (url 指向新 Gemini.js)
        if 'ChatGPT-App-Check' in data.get('script-providers', {}):
            provider = data['script-providers'].pop('ChatGPT-App-Check')
            provider['url'] = GEMINI_JS_URL
            data['script-providers']['Gemini-Check'] = provider
            changed = True
            print("🔧 Provider 替换完成: ChatGPT-App-Check → Gemini-Check (url 指向 Gemini.js)")

        if changed:
            new_content = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
            with open(ST_FILE, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ 已更新 {ST_FILE}")
        else:
            print(f"✅ {ST_FILE} 无需更新")
    except yaml.YAMLError as e:
        print(f"❌ YAML 错误: {e}")

# ===== 2. 修改 collapsed-tiles/script/Gemini.js (从初始 JS 复制 + 改 URL) =====
if not os.path.exists(GEMINI_JS):
    initial_js = """async function request(method, params) {
  return new Promise((resolve, reject) => {
    const httpMethod = $httpClient[method.toLowerCase()];
    httpMethod(params, (error, response, data) => {
      resolve({ error, response, data });
    });
  });
}

async function main() {
  const { error, response, data } = await request(
    "GET",
    "https://ios.chat.openai.com"
  );

  if (error) {
    $done({
      content: "Network Error",
      backgroundColor: "",
    });
    return;
  }

  if (data.toLowerCase().includes("disallowed isp")) {
    $done({
      content: "Disallowed ISP",
      backgroundColor: "",
    });
    return;
  }

  if (data.toLowerCase().includes("been blocked")) {
    $done({
      content: "Blocked",
      backgroundColor: "",
    });
    return;
  }

  $done({
    content: `Available`,
    backgroundColor: "#88A788",
  });
}

(async () => {
  main()
    .then((_) => {})
    .catch((error) => {
      $done({});
    });
})();
"""
    download_initial_file(GEMINI_JS, UPSTREAM_JS_RAW, initial_js)

if os.path.exists(GEMINI_JS):
    with open(GEMINI_JS, "r", encoding="utf-8") as f:
        js_content = f.read()

    original_js = js_content

    # 精确替换请求 URL 为 Gemini (逻辑一模一样)
    js_content = re.sub(r'"https://ios\.chat\.openai\.com"', f'"{GEMINI_URL}"', js_content)

    if js_content != original_js:
        with open(GEMINI_JS, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"✅ 已更新 {GEMINI_JS} 为 Gemini 检测")
    else:
        print(f"✅ {GEMINI_JS} 无需更新")

print("✨ 所有修改完成")
