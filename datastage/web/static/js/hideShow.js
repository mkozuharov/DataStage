
/* hide/show for upload form */

$(document).ready(function() {



 
  var showHide = function() { 
      
    
      if ($(this).hasClass("collapsed")) {
        $(this).siblings("div.panel").slideDown('fast');
        $(this).siblings("div.panel").removeClass('collapsed');    
        $(this).removeClass('collapsed');    
      }
      else {
        $(this).siblings("div.panel").slideUp('fast');
        $(this).siblings("div.panel").addClass('collapsed'); 
        $(this).addClass('collapsed');  
      }
      
      
      
      return false;
  }
  
 /*
 
  $('form.upload label').click(showHide);
  $('form.upload label').addClass('collapsible');
  $('form.upload label').addClass('collapsed');
  $('form.upload div.panel').addClass('collapsible');
  $('form.upload div.panel').addClass('collapsed');
 
 */


  $('div.actions form label').click(showHide);
  $('div.actions form label').addClass('collapsible');
  $('div.actions form label').addClass('collapsed');
  $('div.actions form div.panel').addClass('collapsible');
  $('div.actions form div.panel').addClass('collapsed');


/* 
 
 
  $('form.upload div.panel').hide(); 
  $('form.upload label').click(function() { 
    $(this).siblings('div').slideToggle('fast').siblings('ul:visible').slideUp('fast');
    return false; 
  }); 
  

 */
 
 
});


 