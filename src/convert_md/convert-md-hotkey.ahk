#Requires AutoHotkey v2.0
#SingleInstance Force

; convert-md hotkey (default Ctrl+Alt+M). Installed by "convert-md setup", which
; copies this script to %LOCALAPPDATA%\ConvertMd and writes convert-md.ini beside it.

CONFIG := A_ScriptDir "\convert-md.ini"
PYTHONW := IniRead(CONFIG, "convert-md", "pythonw", "")
HOTKEY_KEYS := IniRead(CONFIG, "convert-md", "hotkey", "^!m")
MD_EXTENSIONS := ["md", "markdown"]

if (PYTHONW = "" || !FileExist(PYTHONW)) {
    MsgBox("convert-md can't find Python.`n`nRun this in PowerShell to repair it:`n    py -m convert_md setup",
        "convert-md", "Icon!")
    ExitApp
}

HotIf(ExplorerOrDesktopActive)
Hotkey(HOTKEY_KEYS, (*) => ShowConvertMdMenu())
HotIf()

ExplorerOrDesktopActive(*) {
    return WinActive("ahk_class CabinetWClass") || WinActive("ahk_class ExploreWClass")
        || WinActive("ahk_class Progman") || WinActive("ahk_class WorkerW")
}

ShowConvertMdMenu() {
    if (WinActive("ahk_class Progman") || WinActive("ahk_class WorkerW")) {
        Notify("convert-md: the hotkey works in File Explorer windows.`nOn the desktop, right-click the file instead.")
        return
    }
    files := GetSelectedFiles()
    if (files.Length = 0) {
        Notify("convert-md: nothing selected")
        return
    }

    ; Split the selection: Markdown files go out to other formats,
    ; everything else comes in to Markdown.
    mdFiles := []
    otherFiles := []
    for file in files {
        SplitPath(file, , , &ext)
        if IsMarkdownExt(ext)
            mdFiles.Push(file)
        else
            otherFiles.Push(file)
    }

    convertMenu := Menu()
    if (mdFiles.Length > 0) {
        convertMenu.Add("Word", (*) => RunConvert(mdFiles, "docx"))
        convertMenu.Add("PDF", (*) => RunConvert(mdFiles, "pdf"))
        convertMenu.Add("Excel (tables only)", (*) => RunConvert(mdFiles, "xlsx"))
        convertMenu.Add("PowerPoint", (*) => RunConvert(mdFiles, "pptx"))
        convertMenu.Add("Web page", (*) => RunConvert(mdFiles, "html"))
        convertMenu.Add()
        convertMenu.Add("All formats", (*) => RunConvert(mdFiles, "all"))
        convertMenu.Add("As set in the file", (*) => RunConvert(mdFiles, "auto"))
    }
    if (otherFiles.Length > 0) {
        if (mdFiles.Length > 0) {
            convertMenu.Add()
            convertMenu.Add("Convert the " otherFiles.Length " non-Markdown file(s) to Markdown", (*) => RunConvert(otherFiles, "md"))
        } else {
            convertMenu.Add("Convert to Markdown", (*) => RunConvert(otherFiles, "md"))
        }
    }
    convertMenu.Show()
}

Notify(text) {
    ToolTip(text)
    SetTimer(() => ToolTip(), -2000)
}

IsMarkdownExt(ext) {
    for mdExt in MD_EXTENSIONS {
        if (StrLower(ext) = mdExt)
            return true
    }
    return false
}

; Same command the right-click menu uses. -P keeps the current folder off Python's import path.
RunConvert(files, toValue) {
    for file in files
        Run(Format('"{1}" -P -m convert_md --gui --to {2} "{3}"', PYTHONW, toValue, file))
}

; Selected files in the active Explorer tab only. Folders are skipped.
GetSelectedFiles() {
    paths := []
    win := GetActiveExplorerTab(WinActive("A"))
    if !IsObject(win)
        return paths
    try {
        for item in win.Document.SelectedItems() {
            path := item.Path
            attrs := FileExist(path)
            if (attrs != "" && !InStr(attrs, "D"))
                paths.Push(path)
        }
    }
    return paths
}

; On Windows 11 every tab in an Explorer window has the same HWND, so match
; the active tab (ShellTabWindowClass1) against each shell view's own window.
GetActiveExplorerTab(hwnd) {
    static IID_IShellBrowser := "{000214E2-0000-0000-C000-000000000046}"
    activeTab := 0
    try activeTab := ControlGetHwnd("ShellTabWindowClass1", hwnd)
    for win in ComObject("Shell.Application").Windows() {
        try {
            if (win.HWND != hwnd)
                continue
        } catch {
            continue
        }
        if activeTab {
            thisTab := 0
            try {
                shellBrowser := ComObjQuery(win, IID_IShellBrowser, IID_IShellBrowser)
                ComCall(3, shellBrowser, "uint*", &thisTab)   ; IOleWindow::GetWindow
            } catch {
                continue
            }
            if (thisTab != activeTab)
                continue
        }
        return win
    }
    return 0
}
