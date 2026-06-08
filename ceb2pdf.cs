using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

class Ceb2Pdf
{
    // ==================== P/Invoke ====================
    [DllImport("user32.dll", EntryPoint="SendMessageW", CharSet=CharSet.Unicode)]
    static extern IntPtr SendStr(IntPtr h, uint msg, IntPtr w, string l);
    [DllImport("user32.dll")]
    static extern bool PostMessage(IntPtr h, uint msg, IntPtr w, IntPtr l);
    [DllImport("user32.dll")]
    static extern IntPtr FindWindowEx(IntPtr p, IntPtr a, string cls, string wnd);
    [DllImport("user32.dll")]
    static extern bool EnumChildWindows(IntPtr p, WndProc cb, IntPtr lp);
    [DllImport("user32.dll")]
    static extern bool EnumWindows(WndProc cb, IntPtr lp);
    [DllImport("user32.dll", CharSet=CharSet.Auto)]
    static extern int GetClassName(IntPtr h, StringBuilder sb, int max);
    [DllImport("user32.dll", CharSet=CharSet.Auto)]
    static extern int GetWindowText(IntPtr h, StringBuilder sb, int max);
    [DllImport("user32.dll")]
    static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")]
    static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")]
    static extern int GetDlgCtrlID(IntPtr h);
    [DllImport("user32.dll")]
    static extern bool SetWindowPos(IntPtr h, IntPtr insertAfter, int x, int y, int cx, int cy, uint flags);
    [DllImport("user32.dll")]
    static extern bool ShowWindow(IntPtr h, int cmd);

    // **CreateProcess + STARTF_USESHOWWINDOW**：真正阻止 c2pfree 创建可见窗口——
    // 之前用 .NET `ProcessStartInfo { WindowStyle = Hidden }` 对 WinForms GUI 程序无效
    // （c2pfree 用 Form.Show()，不是 alloc console，.NET 隐藏属性不生效）。
    [StructLayout(LayoutKind.Sequential)]
    struct STARTUPINFO
    {
        public int cb;
        public string lpReserved;
        public string lpDesktop;
        public string lpTitle;
        public int dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute;
        public int dwFlags;
        public short wShowWindow;
        public short cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct PROCESS_INFORMATION
    {
        public IntPtr hProcess;
        public IntPtr hThread;
        public int dwProcessId;
        public int dwThreadId;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct SECURITY_ATTRIBUTES
    {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        public int bInheritHandle;
    }

    const int STARTF_USESHOWWINDOW = 0x00000001;
    const int STARTF_USESTDHANDLES = 0x00000100;
    const short SW_HIDE = 0;
    const short SW_SHOWNORMAL = 1;
    const uint CREATE_NO_WINDOW = 0x08000000;
    const uint EXTENDED_STARTUPINFO_PRESENT = 0x00080000;
    const uint INHERIT_CALLER_PRIORITY = 0x00000002;

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool CreateProcess(
        string lpApplicationName,
        string lpCommandLine,
        IntPtr lpProcessAttributes,
        IntPtr lpThreadAttributes,
        bool bInheritHandles,
        uint dwCreationFlags,
        IntPtr lpEnvironment,
        string lpCurrentDirectory,
        ref STARTUPINFO lpStartupInfo,
        out PROCESS_INFORMATION lpProcessInformation);

    [DllImport("kernel32.dll")]
    static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

    [DllImport("kernel32.dll")]
    static extern bool GetExitCodeProcess(IntPtr hProcess, out uint lpExitCode);

    [DllImport("kernel32.dll")]
    static extern bool CloseHandle(IntPtr hObject);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr CreateFile(
        string lpFileName, uint dwDesiredAccess, uint dwShareMode,
        IntPtr lpSecurityAttributes, uint dwCreationDisposition,
        uint dwFlagsAndAttributes, IntPtr hTemplateFile);

    delegate bool WndProc(IntPtr h, IntPtr lp);

    static readonly IntPtr HWND_TOP = IntPtr.Zero;
    const uint SWP_NOACTIVATE = 0x0010;
    const uint SWP_NOZORDER = 0x0004;
    const uint SWP_NOSIZE = 0x0001;
    const uint SWP_HIDEWINDOW = 0x0080;

    const uint WM_SETTEXT = 0x000C;
    const uint WM_COMMAND = 0x0111;
    const uint WM_KEYDOWN = 0x0100;
    const uint WM_KEYUP = 0x0101;
    const int VK_RETURN = 0x0D;

    // ==================== Logic ====================
    static void Log(string m) { Console.Error.WriteLine("[ceb2pdf] " + m); }

    static void HideWindow(IntPtr h)
    {
        // 多重保险隐藏窗口：SW_HIDE（=0）彻底隐藏 + SWP_HIDEWINDOW 移出可见区。
        ShowWindow(h, SW_HIDE);
        SetWindowPos(h, HWND_TOP, -10000, -10000, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_HIDEWINDOW);
    }

    static IntPtr FindDialog(int pid)
    {
        IntPtr found = IntPtr.Zero;
        EnumWindows((h, l) =>
        {
            if (!IsWindowVisible(h)) return true;
            uint wpid;
            GetWindowThreadProcessId(h, out wpid);
            if (wpid != pid) return true;
            var cn = new StringBuilder(256);
            GetClassName(h, cn, 256);
            if (cn.ToString() == "#32770")
            {
                var wn = new StringBuilder(256);
                GetWindowText(h, wn, 256);
                string title = wn.ToString();
                if (!title.Contains("c2p") && title.Length > 0 && title.Length < 20)
                {
                    found = h;
                    return false;
                }
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    /// <summary>用 CreateProcess + STARTF_USESHOWWINDOW 启动 c2pfree，**阻止它创建可见窗口**。</summary>
    static IntPtr LaunchHidden(string exePath, out PROCESS_INFORMATION pi)
    {
        var si = new STARTUPINFO();
        si.cb = Marshal.SizeOf(typeof(STARTUPINFO));
        si.dwFlags = STARTF_USESHOWWINDOW;
        si.wShowWindow = SW_HIDE;

        string cmdLine = "\"" + exePath + "\"";
        bool ok = CreateProcess(
            null, cmdLine, IntPtr.Zero, IntPtr.Zero, false,
            CREATE_NO_WINDOW, IntPtr.Zero, null,
            ref si, out pi);

        if (!ok)
        {
            int err = Marshal.GetLastWin32Error();
            Log("ERROR: CreateProcess 失败 err=" + err);
            pi = new PROCESS_INFORMATION();
            return IntPtr.Zero;
        }
        return pi.hProcess;
    }

    static int ConvertFile(string inputFile, string outputFile)
    {
        string selfDir = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location);
        string exePath = Path.Combine(selfDir, "c2pfree.exe");

        if (!File.Exists(inputFile)) { Log("ERROR: Not found: " + inputFile); return 1; }
        if (!File.Exists(exePath)) { Log("ERROR: c2pfree.exe not found at " + exePath); return 1; }

        string expectedOutput = Path.ChangeExtension(inputFile, ".pdf");

        // Kill existing
        foreach (var p in Process.GetProcessesByName("c2pfree")) try { p.Kill(); } catch { }
        Thread.Sleep(300);

        Log("Input:  " + inputFile);
        Log("Output: " + (outputFile ?? expectedOutput));

        // **用 CreateProcess 启动 c2pfree 并隐藏窗口**
        PROCESS_INFORMATION pi;
        IntPtr hProc = LaunchHidden(exePath, out pi);
        if (hProc == IntPtr.Zero) return 1;

        // 等 c2pfree 启动 + 初始化
        Thread.Sleep(2000);

        // 找 c2pfree 主窗口
        IntPtr mainWnd = IntPtr.Zero;
        for (int i = 0; i < 20; i++)
        {
            EnumWindows((h, l) =>
            {
                if (!IsWindowVisible(h)) return true;
                uint wpid;
                GetWindowThreadProcessId(h, out wpid);
                if (wpid != pi.dwProcessId) return true;
                mainWnd = h;
                return false;
            }, IntPtr.Zero);
            if (mainWnd != IntPtr.Zero) break;
            Thread.Sleep(300);
        }
        if (mainWnd == IntPtr.Zero)
        {
            Log("ERROR: No window (c2pfree 启动后 6s 内未出现主窗口。可能缺 VC++ Runtime 或 .NET 4.x)");
            CloseHandle(pi.hThread);
            CloseHandle(pi.hProcess);
            return 1;
        }

        // **立刻隐藏**——比之前早（c2pfree 启动后 2s 就藏，不要等用户看到）
        HideWindow(mainWnd);

        // Get buttons
        var buttons = new List<IntPtr>();
        var buttonIDs = new List<int>();
        EnumChildWindows(mainWnd, (h, l) =>
        {
            var cn = new StringBuilder(256);
            GetClassName(h, cn, 256);
            if (cn.ToString() == "Button")
            {
                buttons.Add(h);
                buttonIDs.Add(GetDlgCtrlID(h));
            }
            return true;
        }, IntPtr.Zero);

        if (buttons.Count < 4) { Log("ERROR: Not enough buttons (got " + buttons.Count + ", need 4)"); try { Process.GetProcessById(pi.dwProcessId).Kill(); } catch { } return 1; }

        // Click same directory
        PostMessage(mainWnd, WM_COMMAND, (IntPtr)(buttonIDs[3] & 0xFFFF), buttons[3]);
        Thread.Sleep(300);

        // Click convert
        Log("Converting...");
        PostMessage(mainWnd, WM_COMMAND, (IntPtr)(buttonIDs[0] & 0xFFFF), buttons[0]);
        Thread.Sleep(1500);

        // Find file dialog
        IntPtr dialog = IntPtr.Zero;
        for (int i = 0; i < 20; i++)
        {
            Thread.Sleep(300);
            dialog = FindDialog(pi.dwProcessId);
            if (dialog != IntPtr.Zero) break;
        }
        if (dialog == IntPtr.Zero) { Log("ERROR: No dialog"); try { Process.GetProcessById(pi.dwProcessId).Kill(); } catch { } return 1; }

        // Move dialog off-screen
        HideWindow(dialog);

        // Find edit box
        IntPtr comboEx = FindWindowEx(dialog, IntPtr.Zero, "ComboBoxEx32", null);
        IntPtr edit = IntPtr.Zero;
        if (comboEx != IntPtr.Zero)
        {
            IntPtr combo = FindWindowEx(comboEx, IntPtr.Zero, "ComboBox", null);
            if (combo != IntPtr.Zero)
                edit = FindWindowEx(combo, IntPtr.Zero, "Edit", null);
        }
        if (edit == IntPtr.Zero) { Log("ERROR: No edit box"); try { Process.GetProcessById(pi.dwProcessId).Kill(); } catch { } return 1; }

        // Set filename and press Enter
        SendStr(edit, WM_SETTEXT, IntPtr.Zero, inputFile);
        Thread.Sleep(300);
        PostMessage(edit, WM_KEYDOWN, (IntPtr)VK_RETURN, IntPtr.Zero);
        Thread.Sleep(30);
        PostMessage(edit, WM_KEYUP, (IntPtr)VK_RETURN, IntPtr.Zero);

        // Wait for conversion
        var sw = Stopwatch.StartNew();
        bool ok = false;
        long lastSz = -1;
        int stable = 0;

        while (sw.ElapsedMilliseconds < 180000)
        {
            Thread.Sleep(500);
            if (File.Exists(expectedOutput))
            {
                try
                {
                    var fi = new FileInfo(expectedOutput);
                    if (fi.Length > 0)
                    {
                        if (fi.Length == lastSz) { stable++; if (stable >= 3) { ok = true; break; } }
                        else { stable = 0; lastSz = fi.Length; }
                    }
                }
                catch { }
            }
            // 用 WaitForSingleObject 检查 c2pfree 是否退出
            uint waitRes = WaitForSingleObject(hProc, 0);
            if (waitRes == 0)  // WAIT_OBJECT_0: 进程已退出
            {
                Thread.Sleep(500);
                if (File.Exists(expectedOutput) && new FileInfo(expectedOutput).Length > 0) ok = true;
                break;
            }
        }

        // 清理：关 c2pfree 进程
        try { Process.GetProcessById(pi.dwProcessId).Kill(); } catch { }
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);

        if (ok && File.Exists(expectedOutput))
        {
            if (!string.IsNullOrEmpty(outputFile) && outputFile != expectedOutput)
            {
                try
                {
                    string outDir = Path.GetDirectoryName(outputFile);
                    if (!string.IsNullOrEmpty(outDir) && !Directory.Exists(outDir))
                        Directory.CreateDirectory(outDir);
                    File.Copy(expectedOutput, outputFile, true);
                    File.Delete(expectedOutput);
                    expectedOutput = outputFile;
                }
                catch (Exception ex) { Log("Copy error: " + ex.Message); }
            }
            Log("OK: " + new FileInfo(expectedOutput).Length + " bytes");
            Console.WriteLine(expectedOutput);
            return 0;
        }
        Log("FAILED");
        return 1;
    }

    static int Main(string[] args)
    {
        if (args.Length < 1 || args[0] == "-h" || args[0] == "--help")
        {
            Console.Error.WriteLine("CEB/CEBX to PDF Converter");
            Console.Error.WriteLine("Usage: ceb2pdf <input> [output.pdf]");
            Console.Error.WriteLine("       ceb2pdf <input1> <input2> ...");
            return 1;
        }

        // Single file mode
        if (args.Length <= 2)
        {
            string input = Path.GetFullPath(args[0]);
            string output = args.Length > 1 ? Path.GetFullPath(args[1]) : null;
            return ConvertFile(input, output);
        }

        // Batch mode
        int success = 0, fail = 0;
        foreach (string arg in args)
        {
            string input = Path.GetFullPath(arg);
            if (ConvertFile(input, null) == 0) success++;
            else fail++;
        }
        Log("Done: " + success + " OK, " + fail + " failed");
        return fail > 0 ? 1 : 0;
    }
}
