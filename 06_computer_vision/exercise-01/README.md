# Exercise 1

## Original notebook run

- [notebook with output cells](../docs_from_teacher/Notebooks/13%20YOLO%20ultralytics.ipynb)

output of run:
zidane with boxes and predictions

![zidane with boxes and predictions](../docs_from_teacher/Notebooks/runs/detect/predict/zidane.jpg)

bus with boxes and predictions

![bus with boxes and predictions](../docs_from_teacher/Notebooks/runs/detect/predict-2/bus.jpg)

## run with my photo

- [notebook with output cells](../docs_from_teacher/Notebooks/13%20YOLO%20ultralytics%20my%20photo.ipynb)
output of run

prediction with yolo

![prediction with yolo](../docs_from_teacher/Notebooks/runs-my-photo/detect/predict/my_photo.jpg)

prediction with COCO

![prediction with COCO](../docs_from_teacher/Notebooks/runs-my-photo/detect/predict-2/my_photo.jpg)

## conclusion

- YOLO detected 2 persons and a tie
- in my photo there was a potted plant that was not detected, probably the shape could be put of the yolo specifications
- also there was a kind of plant that was not in a pot, but I think yolo consider it since it cannot fully determine deepness in a photo, like there was a pot in front and probably that made it think both plants were in pots
- Both CLI and `model(...)` cells were good at prediction
- The only thing it was not properly detected was a trash can that was labeled as a vase instead

## Optional challenge

prediction with yolo and `conf=0.7`

![prediction with yolo and conf 0.7](../docs_from_teacher/Notebooks/runs-optional/detect/predict/my_photo.jpg)

as you can see, there was no object detected

prediction with yolo and `model=yolov8s.pt`

![prediction with yolo and model yolov8s.pt](../docs_from_teacher/Notebooks/runs-optional/detect/predict-2/my_photo.jpg)

as you can see, there is less objects labeled but with a better prediction

prediction with yolo for video

![prediction with yolo for video](../docs_from_teacher/Notebooks/runs-video/detect/predict/my_video.mp4)

it is difficult to see a wrong label in the video, but from the output in the cell of the notebook I saw there was a frame were it labeled the left dog as a bird
