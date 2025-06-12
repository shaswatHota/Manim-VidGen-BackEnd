from manim import *

class BubbleSortVisualization(Scene):
    def construct(self):
        # 1. Introduction Scene (0s–3s)
        title = Text("Bubble Sort Visualization", font_size=48)
        self.play(FadeIn(title))
        self.wait(2)
        self.play(FadeOut(title))

        # 2. Initial Array Display (3s–6s)
        arr = [5, 2, 4, 6, 1, 3]
        bars = []
        labels = []
        for i, val in enumerate(arr):
            bar = Rectangle(width=0.5, height=val, fill_opacity=0.8, color=BLUE)
            label = Text(str(val), font_size=24)
            label.next_to(bar, UP)
            group = Group(bar, label)
            bars.append(bar)
            labels.append(label)

        group_bars = Group(*bars).arrange(RIGHT, buff=0.5).move_to(ORIGIN)
        group_labels = Group(*labels)

        self.play(FadeIn(group_bars, group_labels))
        self.wait(1)

        # 3. Bubble Sort Process (6s–18s)
        n = len(arr)
        for i in range(n - 1):
            pass_text = Text(f"Pass: {i + 1}", font_size=24).to_edge(UP)
            self.play(Write(pass_text))
            for j in range(n - i - 1):
                comparing_text = Text(f"Comparing: {arr[j]} and {arr[j+1]}", font_size=24).to_edge(UP)
                self.play(Transform(pass_text, comparing_text))

                bar1 = bars[j]
                bar2 = bars[j + 1]
                self.play(bar1.animate.set_color(RED), bar2.animate.set_color(RED))
                self.wait(0.5)

                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]

                    # Animate swap
                    temp_pos = bar1.get_center()
                    self.play(
                        bar1.animate.move_to(bar2.get_center()),
                        bar2.animate.move_to(temp_pos)
                    )

                    # Update bars list
                    bars[j], bars[j + 1] = bars[j + 1], bars[j]

                    # Update labels
                    labels[j].become(Text(str(arr[j]), font_size=24).next_to(bars[j], UP))
                    labels[j+1].become(Text(str(arr[j+1]), font_size=24).next_to(bars[j+1], UP))
                    self.play(FadeIn(labels[j]), FadeIn(labels[j+1]))

                self.play(bar1.animate.set_color(BLUE), bar2.animate.set_color(BLUE))
                self.wait(0.5)
            self.play(FadeOut(pass_text))

        # 4. Sorted Array Display (18s–20s)
        self.play(*[bar.animate.set_color(GREEN) for bar in bars])
        sorted_text = Text("Sorted!", font_size=36).next_to(group_bars, DOWN)
        self.play(Write(sorted_text))
        self.wait(2)

        # 5. Conclusion Scene (20s–23s)
        self.play(FadeOut(group_bars, group_labels, sorted_text))
        conclusion_text = Text("Bubble Sort: A Simple Sorting Algorithm", font_size=48).move_to(ORIGIN)
        self.play(Write(conclusion_text))
        self.wait(2)
        self.play(FadeOut(conclusion_text))