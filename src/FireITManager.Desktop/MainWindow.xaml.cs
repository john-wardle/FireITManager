using FireITManager.Desktop.ViewModels;
using System.ComponentModel;
using System.Windows;

namespace FireITManager.Desktop;

public partial class MainWindow : Window
{
    private readonly MainWindowViewModel _viewModel;

    public MainWindow()
    {
        InitializeComponent();
        _viewModel = new MainWindowViewModel();
        DataContext = _viewModel;
    }

    protected override async void OnClosing(CancelEventArgs e)
    {
        await _viewModel.DisposeAsync();
        base.OnClosing(e);
    }
}
