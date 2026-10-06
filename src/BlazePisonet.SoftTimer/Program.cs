namespace BlazePisonet.SoftTimer;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        using var mutex = new Mutex(true, @"Global\BlazePisonetSoftTimer", out var created);
        if (!created) return;

        ApplicationConfiguration.Initialize();
        Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
        Application.ThreadException += (_, e) => Storage.Log("UI exception: " + e.Exception);
        AppDomain.CurrentDomain.UnhandledException += (_, e) => Storage.Log("Unhandled exception: " + e.ExceptionObject);

        try
        {
            var config = Storage.LoadConfig();
            using var controller = new AppController(config);
            using var main = new MainForm(controller);
            Application.Run(main);
        }
        catch (Exception ex)
        {
            Storage.Log("Fatal startup exception: " + ex);
            MessageBox.Show(ex.ToString(), "BlazePisonet SoftTimer could not start", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
