"""
This script takes in a .json file from the Chrome devtools performance timeline,
and outputs an HTML file with a visualization of the layout shifts in filmstrips.

It has one major limitation currently: I'm not sure how to scale from the real
viewport size to the size of the images in filmstrips. For the recordings I'm
doing, I used the "Moto G4" preset, which sets the viewport to 360x640 and
produces 280x498 filmstrip images. I set the scale() function to use a constant
based on that, but you may need to adjust to your use case.
"""
import json
import sys

def main():
  if len(sys.argv) != 3:
    print "Usage: python layoutshifts.py <devtools-performance-trace-filename> <output-filename>"
    sys.exit()

  trace_filename = sys.argv[1]
  with open(trace_filename) as trace_file:
    trace_data = json.load(trace_file)
  screenshots, shifts, navigation_start, site_url = parse_trace(trace_data)
  html_out = generate_html(screenshots, shifts, navigation_start, site_url)

  with open(sys.argv[2], 'w') as outfile:
    outfile.write(html_out)

def scale(val):
  return int(val * 0.778)

def shift_rect_html(node, is_new):
  rect = node['new_rect'] if is_new else node['old_rect']
  return """<div style="
    position: absolute;
    left: %dpx;
    top: %dpx;
    width: %dpx;
    height: %dpx;"
    class="shift-rect-%s"
    title="Shifted from %d, %d, %d, %d to %d, %d, %d, %d (top, left, width, height)"></div>""" % (
      scale(rect[0]),
      scale(rect[1]),
      scale(rect[2]),
      scale(rect[3]),
      'new' if is_new else 'old',
      node['old_rect'][0],
      node['old_rect'][1],
      node['old_rect'][2],
      node['old_rect'][3],
      node['new_rect'][0],
      node['new_rect'][1],
      node['new_rect'][2],
      node['new_rect'][3])

def region_rect_html(rects):
  html = ''
  for rect in rects:
    html += """<div style="
      position: absolute;
      left: %dpx;
      top: %dpx;
      width: %dpx;
      height: %dpx;"
      class="region-rect"
      title="Region for shift: %d, %d, %d, %d (top, left, width, height)"></div>""" % (
        scale(rect[0]),
        scale(rect[1]),
        scale(rect[2]),
        scale(rect[3]),
        rect[0],
        rect[1],
        rect[2],
        rect[3]
      )
  return html

def shifts_before_timestamp(index, ts, all_shifts, is_new):
  html = ''
  scores = []
  have_data = False
  while index < len(all_shifts) and all_shifts[index]['ts'] <= ts:
    shift = all_shifts[index]
    if is_new:
      html += region_rect_html(shift['args']['data']['region_rects'])
    for node in shift['args']['data']['impacted_nodes']:
      html += shift_rect_html(node, is_new)
      have_data = True
    scores.append("Score: %f" % (shift['args']['data']['score']))
    index += 1
  if is_new:
    html += '<div class="score-sumary">%s</div>' % '<br>'.join(scores)
  return (index, html, have_data)

def generate_filmstrip(screenshots, shifts, shorten, navigation_start):
  html_out = '<div class="container">'
  old_shift_index = 0
  new_shift_index = 0
  last_screenshot_data = ''
  for screenshot, next_screenshot in zip(screenshots, screenshots[1:]):
    if screenshot['ts'] < navigation_start:
      continue
    old_shift_index, old_shift, have_old_data = shifts_before_timestamp(
        old_shift_index, next_screenshot['ts'], shifts, False)
    new_shift_index, new_shift, have_new_data = shifts_before_timestamp(
        new_shift_index, screenshot['ts'], shifts, True)
    if shorten and not have_old_data and not have_new_data:
      continue
    html_out += '<div class="img-box"><img src="data:image/png;base64,%s">%s%s<div class="timestamp">Time: %d</div></div>\n' % (
        screenshot['snapshot'],
        old_shift,
        new_shift,
        (screenshot['ts'] - navigation_start) / 1000)
  html_out += "</div>"
  return html_out

def parse_trace(trace_data):
  screenshots = []
  shifts = []
  navigation_start = None
  site_url = None
  for item in trace_data:
    if not 'name' in item:
      continue
    if item['name'] == 'Screenshot':
      screenshots.append(
          {'ts': item['ts'], 'snapshot': item['args']['snapshot']})
    if item['name'] == 'LayoutShift':
      shifts.append({'ts': item['ts'], 'args': item['args']})
    if (item['name'] == 'navigationStart' and
        'args' in item and 'data' in item['args'] and
        item['args']['data']['isLoadingMainFrame'] and
            item['args']['data']['documentLoaderURL'].startswith('http')):
      navigation_start = item['ts']
      site_url = item['args']['data']['documentLoaderURL']

  screenshots.sort(key=lambda i: i['ts'])
  if navigation_start is None:
    navigation_start = screenshots[0]['ts']
  shifts.sort(key=lambda i: i['ts'])

  return (screenshots, shifts, navigation_start, site_url)


def generate_html(screenshots, shifts, navigation_start, site_url):
  html_out = """<html>
  <style>
  .container {
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
  }
  .img-box {
    position: relative;
    display: inline-block;
    border: 1px solid black;
  }
  .shift-rect-new {
    border: 1px solid red;
  }
  .shift-rect-old {
    border: 1px solid yellow;
  }
  .region-rect {
    opacity: 0.2;
    background-color: red;
  }
  .score-summary {
  }
  .timestamp {
  }
  img {
    border: 1px solid black;
  }
  </style>
  <body>"""
  if site_url:
    html_out += '<h1>Trace for <a href="%s">%s</a></h1>' % (site_url, site_url)
  html_out += "<h2>Layout shifts</h2>"
  html_out += generate_filmstrip(screenshots, shifts, True, navigation_start)
  html_out += "<h2>Full Filmstrip</h2>"
  html_out += generate_filmstrip(screenshots, shifts, False, navigation_start)
  html_out += '</body></html>'
  return html_out


if __name__ == "__main__":
    main()
