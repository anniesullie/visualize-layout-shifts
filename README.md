# visualize-layout-shifts
A python script I threw together to visualize layout shifts.

There are lots of great tools out there, like [WebPageTest](https://webpagetest.org/) and [SpeedCurve](https://speedcurve.com/blog/visualising-cls-layout-shifts/). But I needed to visualize layout shifts on multiple builds of Chrome, so I threw this together. To run:

1. Make a recording in the [DevTools performance panel](https://developers.google.com/web/tools/chrome-devtools/evaluate-performance) and save it.
2. Run `python layoutshifts.py <your-recording> <output-filename>`
3. Open up the output html file in a browser to view the shifts on a timeline.

## Caveats
I didn't have time to research how devtools scales the filmstrip it records. I used DevTools mobile emulation for Moto G4, which sets the resolution to 360x640 and generates 280x498 filmstrip images, so the `scale()` function just scales for that. Will need to be modified to work in all cases!
