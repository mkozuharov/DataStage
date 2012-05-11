
/* hide/show for upload form */

$(document).ready(function() {
	var redisplay = function() {
		$(this).css('display', 'block');
	}
	var showHide = function() {
		var panel = $(this).siblings("div.panel");
		if (panel.hasClass("collapsed")) {
			panel.slideDown('fast');
			panel.removeClass('collapsed');
			$(document).click(hideOtherPanels).focus(hideOtherPanels);
		} else {
			panel.slideUp('fast', redisplay);
			panel.addClass('collapsed');
		}
		return false;
	}
	var hideOtherPanels = function(e) {
		if (e.target == document) return; // document gets focus when file choose dialog closes
		var panel = $(e.target).closest('div.panel-group').find('div.panel');
		$('div.panel').not(panel).each(function() {
			var panel = $(this);
			if (!panel.hasClass("collapsed"))
				panel.addClass("collapsed").slideUp("fast", redisplay);
		});
		$(document).unbind('click', hideOtherPanels).unbind('focus', hideOtherPanels)
	};

  
 /*
 
  $('form.upload label').click(showHide);
  $('form.upload label').addClass('collapsible');
  $('form.upload label').addClass('collapsed');
  $('form.upload div.panel').addClass('collapsible');
  $('form.upload div.panel').addClass('collapsed');
 
 */


	$('div.panel-group form label').click(showHide);
	$('div.panel-group form div.panel').addClass('collapsible');
	$('div.panel-group form div.panel').addClass('collapsed');

	$('div.panel-group input').focus(function() {
		var panel = $(this).parent();
		if (panel.hasClass("collapsed")) {
			panel.slideDown('fast');
			panel.removeClass('collapsed');
			$('*').focus(hideOtherPanels).click(hideOtherPanels);

		}
	});



/* 
 
 
  $('form.upload div.panel').hide(); 
  $('form.upload label').click(function() { 
    $(this).siblings('div').slideToggle('fast').siblings('ul:visible').slideUp('fast');
    return false; 
  }); 
  

 */
 
 
});


 