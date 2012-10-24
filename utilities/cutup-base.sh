convert base.png -crop 384x64+768+64 +repage hero-brake.png
convert base.png -crop 320x64+0+256 +repage hero-crouch.png
convert base.png -crop 576x64+0+0 +repage hero-idle.png
convert base.png -crop 384x64+640+0 +repage hero-wait.png
convert base.png -crop 640x64+0+64 +repage hero-walk.png
convert base.png -crop 1024x64+0+128 +repage hero-run.png
convert base.png -crop 1088x64+0+192 +repage hero-sprint.png
convert base.png -crop 256x64+512+256 +repage hero-jump.png

convert base.png -crop 64x64 base-tile.png

montage base-tile-84.png \
        base-tile-83.png \
        base-tile-82.png \
        base-tile-81.png \
        base-tile-80.png \
        -tile x1 -geometry 64x64 -background none hero-uncrouch.png

montage base-tile-96.png \
        base-tile-97.png \
        base-tile-98.png \
        -tile x1 -geometry 64x64 -background none hero-die.png

rm base-tile*png
mogrify -filter Lagrange -resize  50% hero-*.png
