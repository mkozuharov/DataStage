/* ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# -------------------------------------------------------------------- */

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
