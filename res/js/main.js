$(function(){ // JQuerry header

    var IsChecked = $('#AutoDefil').is(':checked');
    var AutoScroll = null;

	/* Console updater */
    setInterval(function(){ // Setup a thread who update the console text
        $.ajax({url: '/GetConsole'}).done(function(data) {
            $("#Console").val(data['ConsoleText']);
        });
    }, 50);
	/* End of console updater */
    
	/* Console autodefil */
    $('#AutoDefil').change(function(){ // Check for the "#AutoDefil" checkbox
        IsChecked = $('#AutoDefil').is(':checked');
        if (IsChecked){
            AutoScroll = setInterval(function(){ $('#Console').scrollTop($('#Console')[0].scrollHeight); }, 50); // If the box is checked scroll down every 0.1 seconds
        }else 
        {
            clearInterval(AutoScroll); // Else, stop the AutoScroll thread
        }
    });
    /* End of console autodefil */
	
	/* Console module */
    $('#ConsoleSender').unbind('click').bind('click', function(){
        $.ajax({
			type: 'POST',
			url: '/Console',
			data: { 
				'cmd': $('#CommandInput').val(), 
			},
			success: function(){}
		});
    });
	/* End of Console module */
	
	/* Connect module */
	$('#ConnectRequest').unbind('click').bind('click', function(){
        $.ajax({
			type: 'POST',
			url: '/ConnectPrinter',
			data: { 
				'_SerialPort': $('#SerialPort').val(),
				'_BaudSpeed': $('#BaudSpeed').val()
			},
			success: function(){}
		});
    });
	/* End of connect module */
	
	/* All links triggers */
	$('#RfrshSer').click(function(){$.ajax({url: '/ReFreshSerials'});});
	$('#DscnctPrtr').click(function(){$.ajax({url: '/DisconnectPrinter'});});
	$('#RbootPi').click(function(){$.ajax({url: '/ReBootPi'});});
	$('#ShutPi').click(function(){$.ajax({url: '/DownPi'});});
	$('#StartPrt').click(function(){$.ajax({url: '/StartPrint'});});
	$('#PausePrt').click(function(){$.ajax({url: '/PausePrint'});});
	$('#CancelPrt').click(function(){$.ajax({url: '/CancelPrint'});});
	$('#EmerStop').click(function(){$.ajax({url: '/EmergencyStop'});});
	$('#ATXon').click(function(){$.ajax({url: '/ATXon'});});
	$('#ATXoff').click(function(){$.ajax({url: '/ATXoff'});});
	$('#ClrConsole').click(function(){$.ajax({url: '/ClearConsole'})});
});