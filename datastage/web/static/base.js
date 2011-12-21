$(function() {
  $('.meta-title').each(blurTitle);
  $('.meta-description').each(blurDescription);
  $('.meta-submit').remove();
  //$('.meta-title-header').text($('.meta-title-header').text() + ' (click to edit)');
});

function editTitle() {
  var span = $(this);
  var input = $('<input/>').val(span.text())
                           .attr('name', span.attr('name'))
                           .attr('class', span.attr('class'));
  span.replaceWith(input);
  input.focus().blur(updateMeta(input, blurTitle));
}

function editDescription() {
  var span = $(this);
  var input = $('<textarea/>').text(span.text())
                           .attr('name', span.attr('name'))
                           .attr('class', span.attr('class'));
  span.replaceWith(input);
  input.focus().blur(updateMeta(input, blurDescription));
}

function updateMeta(field, blurFunc) { return function() {
  postData = {};
  postData[field.attr('name')] = field.val();
  postData['csrfmiddlewaretoken'] = $('input[name$="csrfmiddlewaretoken"]').val();
  $.post('', postData);
  blurFunc(null, field);
}; }

function blurTitle(i, input) {
  input = $(input);
  input.replaceWith($('<span/>').text(input.val())
                                .attr('name', input.attr('name'))
                                .attr('class', input.attr('class'))
                                .click(editTitle));
}

function blurDescription(i, input) {
  input = $(input);
  input.replaceWith($('<span/>').text(input.val())
                                .attr('name', input.attr('name'))
                                .attr('class', input.attr('class'))
                                .click(editDescription));
}
