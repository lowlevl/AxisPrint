$(function(){ // JQuerry header
    function scrollToBottom() { // Auto-Scroll the console
      $('#Console').scrollTop($('#Console')[0].scrollHeight);
    }
    var IsChecked = false
    var AutoScroll = null;

    setInterval(function(){ // Setup a thread who update the console text
        $.ajax({url: '/GetConsole'}).done(function(data) {
            $("#Console").val(data['ConsoleText']);
        });
    }, 100);
    
	/* Console autodefil */
    $('#AutoDefil').change(function(){ // Check for the "#AutoDefil" checkbox
        IsChecked = $('#AutoDefil').is(':checked');
        if (IsChecked){
            AutoScroll = setInterval(function(){ scrollToBottom(); }, 100); // If the box is checked scroll down every 0.1 seconds
        }else 
        {
            clearInterval(AutoScroll); // Else, stop the AutoScroll thread
        }
    });
    /* End of console autodefil */
	
	/* Console module */
    $('#ConsoleSender').unbind().click(function(){
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
});