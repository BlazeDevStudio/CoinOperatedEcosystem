// PHX-QA #164: protect the real external-board access-control call path
// from regressing to the old "read exception => false => active-low unlock".
// This is a SOURCE-LINKED STATIC guard, not a real USB/coin hardware test.
using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;

namespace BlazePisonet.SoftTimer;

internal static class ExternalBoardAuthoritySourceGuard
{
    internal static void Run()
    {
        // The workflow invokes the lab from Pisonet/SoftTimer; the second
        // location also supports running it directly from another cwd.
        string[] candidates =
        {
            Path.Combine(Directory.GetCurrentDirectory(), "src",
                "BlazePisonet.SoftTimer", "AppController.cs"),
            Path.GetFullPath(Path.Combine(AppContext.BaseDirectory,
                "..", "..", "..", "..", "..", "src",
                "BlazePisonet.SoftTimer", "AppController.cs"))
        };
        string? sourcePath = candidates.FirstOrDefault(File.Exists);
        if (sourcePath is null)
            throw new FileNotFoundException(
                "Real AppController.cs checkout required; authority regression cannot skip");

        string source = File.ReadAllText(sourcePath);
        Match signature = Regex.Match(source,
            @"\bprivate\s+void\s+UpdateExternalBoard\s*\(\s*\)\s*\{",
            RegexOptions.CultureInvariant);
        if (!signature.Success)
            throw new InvalidOperationException(
                "Cannot locate real UpdateExternalBoard access-control method");

        // Restrict assertions to one method; a safe helper somewhere else
        // cannot compensate for an unsafe call in this actual authority path.
        int cursor = signature.Index + signature.Length;
        int depth = 1;
        while (cursor < source.Length && depth != 0)
        {
            if (source[cursor] == '{') depth++;
            else if (source[cursor] == '}') depth--;
            cursor++;
        }
        if (depth != 0)
            throw new InvalidOperationException(
                "Unbalanced UpdateExternalBoard source; static gate cannot verify");
        string method = source[signature.Index..cursor];

        Match readFailure = Regex.Match(method,
            @"if\s*\(\s*!\s*_serial\s*\.\s*TryGetSignal\s*\(\s*Config\.TimerActiveSignal\s*,\s*out\s+var\s+raw\s*\)\s*\)\s*\{(?<fault>[^{}]*)\}",
            RegexOptions.CultureInvariant | RegexOptions.Singleline);
        if (!readFailure.Success)
            throw new InvalidOperationException(
                "External board lacks an error-aware measured-signal guard");
        string fault = readFailure.Groups["fault"].Value;

        if (!Regex.IsMatch(fault,
                @"_timer\s*\.\s*SetAuthoritativeSeconds\s*\(\s*0\s*,",
                RegexOptions.CultureInvariant)
            || !Regex.IsMatch(fault, @"\breturn\s*;",
                RegexOptions.CultureInvariant))
            throw new InvalidOperationException(
                "Unknown external board signal must deny time and exit before inversion");

        Match inversion = Regex.Match(method,
            @"var\s+active\s*=\s*Config\.TimerActiveHigh\s*\?\s*raw\s*:\s*!\s*raw\s*;",
            RegexOptions.CultureInvariant);
        Match granted = Regex.Match(method,
            @"_timer\s*\.\s*SetAuthoritativeSeconds\s*\(\s*active\s*\?\s*1\s*:\s*0\s*,",
            RegexOptions.CultureInvariant);
        if (!inversion.Success || !granted.Success
            || readFailure.Index + readFailure.Length > inversion.Index
            || inversion.Index > granted.Index)
            throw new InvalidOperationException(
                "External board error branch must precede polarity inversion and grant");

        if (Regex.IsMatch(method, @"_serial\s*\.\s*GetSignal\s*\(",
                RegexOptions.CultureInvariant))
            throw new InvalidOperationException(
                "Legacy bool-only signal API used by external-board authority");

        Console.WriteLine(
            "EXTERNAL_BOARD_CONTROLLER_AUTHORITY_SOURCE_GUARD_PASS: "
            + "real controller source rejects unknown signal before active-low grant; "
            + "static only");
    }
}
