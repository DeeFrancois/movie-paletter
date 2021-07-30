# movie-paletter
Generates color palettes for each frame of a movie. Also allows you to search for a frame in which a chosen color is a dominant color.

![demo](https://github.com/DeeFrancois/movie-paletter/blob/master/ReadmeImages/demo.gif)

<sup><sup> Movie: The Secret Life of Walter Mitty</sup></sup>

<sup> Requires [awthemes 10.4.0](https://sourceforge.net/projects/tcl-awthemes/), download and place into the same folder </sup>
## *Not exactly ready for public use, just trying to get all my working projects uploaded
(Still need to clean up the code, and make the GUI for User friendly)

## Motivation
I wanted to make one of those movie collage posts on Twitter and thought it would be cool if I had a program that made it easy for me to keep to a certain color scheme

## How it works
This is subject to change since this isn't at all User friendly, but so far..
- Open Movie File (only .mp4 works so far)
- Move bottom left slider to change the seek speed and click the Start button
- Choose your desired color and the seeking will automatically pause when it finds a match
- Click the bottom left picture to save the frame

#### Sliders
- Top Left Slider: Keeps track of the current frame number
- Bottom Left Slider: Set seek speed (number of frames to skip)
- Top Right Slider: Difference factor between colors when generating palette (Higher = More distinct colors)
- Bottom Right Slider: Difference threshold for determining a match (Lower = Closer Match)

## Less than obvious functionality
- Click on the result palette to fill the top bar with its RGB values
- You can drag the seek bar to get palettes without pressing Start
- Click the bottom right picture after choosing a color to fill the bottom bar with the difference factors between it and each color of the result palette

# A peek into the process
Originally, the palette was generated by using an algorithm that went through each pixel and returned a list of RGB values sorted by frequency.
This was a problem because it would often result in one color drowning out the rest. Here's an example:

Let's say we have this frame:

![frame](https://github.com/DeeFrancois/movie-paletter/blob/master/ReadmeImages/example_frame.png)

Looking at this frame, the ideal color palette should consist of:
- That gray/beige color in the background
- The color of Walter's shirt
- The color of Cheryl's shirt
- The dark shadows
- The color of the guy's shirt to the right of Cheryl
- and maybe the red from the woman to the left of Walter

But with the original algorithm we get:

![frame](https://github.com/DeeFrancois/movie-paletter/blob/master/ReadmeImages/example_before.png)

Because there are so many dark pixels, it drowns out the colors that stand out to us.
The way to fix this is to simply, coalesce all the dark RGB values into one color on the palette. So now we have this:

![frame](https://github.com/DeeFrancois/movie-paletter/blob/master/ReadmeImages/example_muddy.png)

This is still not what we want. This is the same issue as with the dark pixels but this time we obviously can't just map every non-dark color to one color.
The solution to this was add a difference factor to determine whether an RGB value should be added to the palette. 
So the algorithm just needs to check if the current RGB value has a high enough difference factor when compared with the previous colors. 
<sup>The "Difference factor" is calculated using the equation described [here](https://en.wikipedia.org/wiki/Color_difference)</sup>

And now for the result..

![frame](https://github.com/DeeFrancois/movie-paletter/blob/master/ReadmeImages/example_frame.png)
![frame](https://github.com/DeeFrancois/movie-paletter/blob/master/ReadmeImages/example_after.png)

With a Difference Factor of 30 (which I've found to be the sweet spot) as chosen by the top right slider, we end up getting all the colors we were looking for except the red. 
The red doesn't show up because it is obscured by too many dark pixels. It stands out because it is a bright color, not because it is a common color. 
This may be fixed later on but I don't think it's important.


