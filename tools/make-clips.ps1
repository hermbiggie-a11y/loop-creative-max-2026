# Turn the Firefly stills into 4-second 1080p30 "footage" clips with slow camera moves (ffmpeg zoompan).
# Output: cabana\raw\clipNN-name.mp4
$ErrorActionPreference = 'Stop'
$Loop  = Split-Path $PSScriptRoot -Parent
$stills = Join-Path $Loop 'cabana\assets\stills'
$raw   = Join-Path $Loop 'cabana\raw'
$fps = 30; $dur = 4; $n = $fps * $dur

# move per clip: in = push in, out = pull out, left/right = pan
$moves = @{
  'clip01-pour' = 'in'; 'clip02-ice' = 'in'; 'clip03-beach' = 'right'; 'clip04-can-sand' = 'out';
  'clip05-cooler' = 'in'; 'clip06-waves' = 'left'; 'clip07-ocean-drive' = 'right'; 'clip08-cheers' = 'in';
  'clip09-sunset' = 'out'; 'clip10-hero-can' = 'in'
}
# hero can shot from the master (2:1 -> 16:9 centre crop happens via zoompan)
Copy-Item (Join-Path $Loop 'cabana\_master\hero-flat.png') (Join-Path $stills 'clip10-hero-can.png') -Force

foreach ($f in Get-ChildItem $stills -Include *.jpg, *.png -Recurse) {
  $name = $f.BaseName; $m = $moves[$name]; if (-not $m) { continue }
  switch ($m) {
    'in'    { $z = "min(1.0+0.15*on/$n,1.15)"; $x = 'iw/2-(iw/zoom/2)'; $y = 'ih/2-(ih/zoom/2)' }
    'out'   { $z = "max(1.15-0.15*on/$n,1.0)"; $x = 'iw/2-(iw/zoom/2)'; $y = 'ih/2-(ih/zoom/2)' }
    'left'  { $z = '1.12'; $x = "(iw-iw/zoom)*(1-on/$n)"; $y = 'ih/2-(ih/zoom/2)' }
    'right' { $z = '1.12'; $x = "(iw-iw/zoom)*(on/$n)"; $y = 'ih/2-(ih/zoom/2)' }
  }
  $out = Join-Path $raw "$name.mp4"
  # upscale 2x first so the zoom stays smooth; scale/crop to 16:9 cover
  $vf = "scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,zoompan=z='$z':x='$x':y='$y':d=${n}:s=1920x1080:fps=$fps,format=yuv420p"
  & ffmpeg -v error -y -loop 1 -i $f.FullName -vf $vf -t $dur -c:v libx264 -preset medium -crf 18 -an $out
  Write-Host "made $name ($m)"
}
