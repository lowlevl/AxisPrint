$(function(){ // JQuerry header
	
    var IsChecked = $('#AutoDefil').is(':checked');
    var AutoScroll = null;
	var ConnectionLost = false;
	
	/* Console updater */
    setInterval(function(){ // Setup a thread who update the console text
        $.ajax({
			url: '/Get',
			error: function (Request, ajaxOptions, thrownError) {
                if (ConnectionLost == false){
                        
                    $("#ConnErrorPopUp").html('     \
                    <style>                         \
                        #ConnErrorPopUp {           \
                            background-color: #111; \
                            opacity: 0.80;          \
                            background: DimGray;    \
                            text-align: center;     \
                            position: absolute;     \
                            z-index: 9001;          \
                            top: 0px;               \
                            left: 0px;              \
                            width: 100%;            \
                            height: 100%;           \
                        }                           \
                        #ConnErrorPopUp span{       \
                            width: auto;            \
                        }                           \
                    </style><span>Connection lost or refused... Trying to reconnect.. (' + Request.status + ')</span>'); // If connection losts, showing popup...
                    ConnectionLost = true;
                }
			},
			success: function(Data){
                if ($("#Console").val() == ""){
                    $("#Console").val(Data['NewLines']); // If TextArea is empty..
                }else if(Data['NewLines'] != ""){
                    $("#Console").val($("#Console").val() + Data['NewLines']); // Just add the new line(s) to the TextArea
                }
                
                
				if (ConnectionLost == true){
					ConnectionLost = false;
					$("#ConnErrorPopUp").html("");
				}
			}
		});
    }, 100);
	/* End of console updater */
    
	/* Console autodefil */
    $('#AutoDefil').change(function(){ // Check for the "#AutoDefil" checkbox
        IsChecked = $('#AutoDefil').is(':checked');
        if (IsChecked){
            AutoScroll = setInterval(function(){ $('#Console').scrollTop($('#Console')[0].scrollHeight); }, 50); // If the box is checked scroll down every 0.05 seconds
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
	
	/* Upload module */
	$('#File2Up').bind('change', function(e){
		var FileUp = document.getElementById("File2Up").files[0];
		if (FileUp.name.split('.').pop() != "gcode"){
			alert("Not GCODE");
			return;
		}
		var UpBar = $("#UpBar");
		var DataForm = new FormData();
		DataForm.append("_UploadedFile", FileUp);
		DataForm.append("FileName", FileUp.name);
		DataForm.append("Size", FileUp.size);
		
		//Reset bar
		$("#UpSuccess").text("");
		UpBar.width("0%");
		UpBar.attr("class", "progress-bar progress-bar-info");
		
		
		var oReq = new XMLHttpRequest();
		oReq.onload = function() {
			if (oReq.status == 200) {
				$("#UpSuccess").text("Uploaded!");
				UpBar.width("100%");
				UpBar.attr("class", "progress-bar progress-bar-success");
			} else {
				$("#UpSuccess").text("Error " + oReq.status + " occurred uploading your file");
				UpBar.width("100%");
				UpBar.attr("class", "progress-bar progress-bar-danger");
			}
		};
		
		oReq.upload.onprogress = function(oEvent) {
			if(oEvent.lengthComputable) {
				var Percent = (Math.trunc((oEvent.loaded/oEvent.total)*100) + "%");
				UpBar.width(Percent);
				$("#UpSuccess").text(Percent);
				if(oEvent.total == oEvent.loaded){
					$("#UpSuccess").text("Processing...");
					UpBar.attr("class", "progress-bar progress-bar-warning progress-bar-striped active");
				}
			}
		}
		
		oReq.open("POST", "/UpLoad", true);
		oReq.send(DataForm);
		e.preventDefault();
	});		
	/* End of upload module */
	
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
	$('#ClrConsole').click(function(){$("#Console").val("")});
});