$(function() {
  $('.meta-title').each(blurTitle);
  $('.meta-submit').remove();
  //$('.meta-title-header').text($('.meta-title-header').text() + ' (click to edit)');
});

function editTitle() {
  var span = $(this);
  var input = $('<input/>').val(span.text())
                           .attr('name', span.attr('name'))
                           .attr('class', span.attr('class'));
  span.replaceWith(input);
  input.focus().blur(function() {
    postData = {};
    postData[input.attr('name')] = input.val();
    postData['csrfmiddlewaretoken'] = $('input[name$="csrfmiddlewaretoken"]').val();
    $.post('', postData);
    blurTitle(null, this);
  });
}

function blurTitle(i, e) {
  var input = $(e);
  input.replaceWith($('<span/>').text(input.val())
                                .attr('name', input.attr('name'))
                                .attr('class', input.attr('class'))
                                .click(editTitle));
}                                