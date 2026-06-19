This chat is just discussion. No code. I want to work through an idea and eventually make a design document (less rigor than a full "specification").

I want to build a tool that solves the "how to demo tools" issue. Something lighter weight than Jupyter Notebooks (especially since they are hard to read unrendered) but that fills automatically with updated code. Basically a demo-runner

Current idea I am thinking of:

YAML Front Matter that includes code exe (bash or python?)
Markdown:

THen within the markdown, you write code blocks:

    ```python
    print('Demo code')
    ```

And it will execute it. (Question: Do you think you do something to *not* execute or do something to tell it to execute?)

In the render, it gets rendered like:

<!-- START Block Result. Do not modify. Will be overwritten -->
```text
OUTPUT
```
<!-- END block result -->

Question: Do you think I do it where you have to have a `print` or `echo`? Or behave more like Jupyter where the last item is pretty-printed if it returned anything? Or settable?

The output will be itself with just the blocks being modified.

I do not want to have to have any special "kernels" but I will have to design it around Python or bash.

On the back end, I am open to ideas of how to process it. One idea is convert it into a single document that has print/echos with blocks to later parse out properly after it is rendered. It should maintain memory across:

    This is a demo:
    
    ```python
    a = 5
    print(a)
    ```
    <!-- START Block Result. Do not modify. Will be overwritten -->
    ```text
    5
    ```
    <!-- END block result -->
    And you can add
    ```python
    print(a + 1)
    ```
    <!-- START Block Result. Do not modify. Will be overwritten -->
    ```text
    6
    ```
    <!-- END block result -->
    
    
I identified some open questions in the above but to explore them more:

### How to handle blocks: 

One idea is to require the "syntax" include `-exe` but since the document itself is "live" (i.e. no export), it may not render. Or require it be started by comments like:

    <!-- EXE -->
    ```python
    a = 5
    print(a)
    ```
    <!-- START Block Result. Do not modify. Will be overwritten -->
    ```text
    5
    ```
    <!-- END block result -->

Or it could follow something kind of like doctest where it has to have a prefix? Discuss
    
### How to handle output

I am torn on Jupyter style outputs vs require print. I am leaning towards optional or always print (maybe pretty-print?). But then you have to be careful because Jupyter only doesn't print if there is a value set. 

I am open to this.