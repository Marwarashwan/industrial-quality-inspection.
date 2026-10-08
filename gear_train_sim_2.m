function gear_train_sim(jsonPath, imageName, refGearId, refDiameterMM, inputTorqueNm)
%GEAR_TRAIN_SIM  Load gear_params.json (from gear_inspector.py) and animate the
%gear train it describes, with real-world scale, correct speed/direction,
%ideal torque/force estimates, true involute tooth profiles, and live
%interactive controls (speed slider + play/pause).
%
%   gear_train_sim(jsonPath, imageName, refGearId, refDiameterMM, inputTorqueNm)
%
%   jsonPath        - path to gear_params.json
%   imageName       - which photo's gears to simulate (must match a field name
%                      from fieldnames(jsondecode(fileread(jsonPath))))
%   refGearId       - id of ONE gear whose real size you know
%   refDiameterMM   - that gear's real outer (tip-to-tip) diameter, in mm
%   inputTorqueNm   - OPTIONAL, default 1 Nm. Assumed torque driving gear #1.
%                      NOT measured from the photo - geometry only, never load.
%
% ASSUMPTIONS / LIMITATIONS (read this before trusting any number it prints):
%   - External spur gears only. Meshing gears are assumed to always spin in
%     opposite directions. Internal/ring gears aren't handled.
%   - Tooth profile is a SIMPLIFIED involute: the flanks follow the real
%     involute-of-a-circle curve (same geometry taught in gear-design courses),
%     but the root fillet is drawn as a straight line + circular arc rather
%     than the true trochoidal curve a manufacturing rack would cut. Good
%     enough to see real tooth shape/meshing visually - NOT a manufacturing
%     drawing.
%   - Pressure angle is fixed at 20 degrees (the common standard) since the
%     photo gives no way to measure it.
%   - Tooth thickness is assumed to be 50% of the angular pitch at the pitch
%     circle (even tooth/gap split) - another assumption the photo can't
%     confirm on its own.
%   - Single input, single load path. Gear id 1 (whichever sorts first) is
%     driven at an arbitrary base speed (adjustable live via the slider) and
%     your chosen torque. A gear not connected to it through any meshing pair
%     stays still and prints a warning.
%   - Torque/force are ideal, lossless (100% efficient, frictionless)
%     estimates - real gear trains always deliver somewhat less. Torque does
%     NOT depend on the slider speed - it only depends on the gear ratios and
%     your chosen input torque, so it's computed once, up front.
%   - Real-world scale depends entirely on your one reference measurement.

if nargin < 5 || isempty(inputTorqueNm)
    inputTorqueNm = 1;
end

%% 1) Load JSON and find this image's data
raw = jsondecode(fileread(jsonPath));
fld = matlab.lang.makeValidName(imageName);
if ~isfield(raw, fld)
    error('Image "%s" not found. Available images: %s', imageName, ...
        strjoin(fieldnames(raw), ', '));
end
imgData = raw.(fld);

if ~isfield(imgData, 'gears') || isempty(imgData.gears)
    error('No confirmed gears were found for "%s".', imageName);
end
gears = imgData.gears;
if ~iscell(gears) && numel(gears) == 1
    gears = {gears};
elseif isstruct(gears)
    gears = arrayfun(@(g) g, gears, 'UniformOutput', false);
end

%% 2) Real-world scale (px -> mm) from one reference gear
pxPerMM = [];
for i = 1:numel(gears)
    g = gears{i};
    if isequal(g.id, refGearId) || (isnumeric(g.id) && g.id == refGearId)
        tipDiamPx = 2 * g.tip_radius_px;
        pxPerMM = tipDiamPx / refDiameterMM;
        break
    end
end
if isempty(pxPerMM)
    error('refGearId %s not found in this image''s gears.', mat2str(refGearId));
end
fprintf('Scale: %.4f px/mm (from reference gear id %s, %.1f mm tip diameter)\n\n', ...
    pxPerMM, mat2str(refGearId), refDiameterMM);

%% 3) Build a gear table in mm
nGears = numel(gears);
id          = cell(nGears, 1);
cx_mm       = zeros(nGears, 1);
cy_mm       = zeros(nGears, 1);
teeth       = zeros(nGears, 1);
pitchR_mm   = zeros(nGears, 1);
tipR_mm     = zeros(nGears, 1);
rootR_mm    = zeros(nGears, 1);

for i = 1:nGears
    g = gears{i};
    id{i}        = g.id;
    cx_mm(i)     = g.cx_px / pxPerMM;
    cy_mm(i)     = g.cy_px / pxPerMM;
    teeth(i)     = g.teeth;
    pitchR_mm(i) = g.pitch_radius_px / pxPerMM;
    tipR_mm(i)   = g.tip_radius_px / pxPerMM;
    % root radius isn't separately measured by the Python side; a standard
    % gear-design approximation is root radius = pitch radius - 1.25*module,
    % with module = 2*pitchR/teeth. Schematic purposes only.
    module = 2 * pitchR_mm(i) / teeth(i);
    rootR_mm(i) = max(0.5 * pitchR_mm(i), pitchR_mm(i) - 1.25 * module);
end

fprintf('Gear table (mm):\n');
fprintf('%-6s %10s %10s %8s %12s %10s\n', 'id', 'cx', 'cy', 'teeth', 'pitchR', 'tipR');
for i = 1:nGears
    fprintf('%-6s %10.2f %10.2f %8d %12.2f %10.2f\n', ...
        mat2str(id{i}), cx_mm(i), cy_mm(i), teeth(i), pitchR_mm(i), tipR_mm(i));
end
fprintf('\n');

%% 4) Propagate speed and direction through meshing_pairs
OMEGA_IN = 60;  % deg/s, arbitrary base speed for gear 1 (slider scales this live)
omega = nan(nGears, 1);
omega(1) = OMEGA_IN;

idxOf = containers.Map();
for i = 1:nGears
    idxOf(matlab.lang.makeValidName(mat2str(id{i}))) = i;
end

edges = [];
if isfield(imgData, 'meshing_pairs') && ~isempty(imgData.meshing_pairs)
    pairs = imgData.meshing_pairs;
    if isstruct(pairs)
        pairs = arrayfun(@(p) p, pairs, 'UniformOutput', false);
    end
    for k = 1:numel(pairs)
        p = pairs{k};
        keyA = matlab.lang.makeValidName(mat2str(p.a));
        keyB = matlab.lang.makeValidName(mat2str(p.b));
        if isKey(idxOf, keyA) && isKey(idxOf, keyB)
            ai = idxOf(keyA);
            bi = idxOf(keyB);
            ratio = teeth(ai) / teeth(bi);
            edges = [edges; ai, bi, ratio]; %#ok<AGROW>
        end
    end
end

changed = true;
while changed
    changed = false;
    for k = 1:size(edges, 1)
        ai = edges(k, 1); bi = edges(k, 2); ratio = edges(k, 3);
        if ~isnan(omega(ai)) && isnan(omega(bi))
            omega(bi) = -omega(ai) * ratio;
            changed = true;
        elseif ~isnan(omega(bi)) && isnan(omega(ai))
            omega(ai) = -omega(bi) / ratio;
            changed = true;
        end
    end
end

fprintf('Speed & direction (gear 1 driven at %d deg/s):\n', OMEGA_IN);
fprintf('%-6s %14s %10s\n', 'id', 'omega(deg/s)', 'note');
for i = 1:nGears
    if isnan(omega(i))
        fprintf('%-6s %14s %10s\n', mat2str(id{i}), 'N/A', 'not connected to gear 1 - stays still');
        omega(i) = 0;
    else
        fprintf('%-6s %14.2f\n', mat2str(id{i}), omega(i));
    end
end
fprintf('\n');

%% 4b) Propagate torque and force (ideal, lossless, ignores the slider)
torqueNm = nan(nGears, 1);
torqueNm(1) = inputTorqueNm;
changed = true;
while changed
    changed = false;
    for k = 1:size(edges, 1)
        ai = edges(k, 1); bi = edges(k, 2); ratio = edges(k, 3);
        if ~isnan(torqueNm(ai)) && isnan(torqueNm(bi))
            torqueNm(bi) = torqueNm(ai) / ratio;
            changed = true;
        elseif ~isnan(torqueNm(bi)) && isnan(torqueNm(ai))
            torqueNm(ai) = torqueNm(bi) * ratio;
            changed = true;
        end
    end
end
forceN = nan(nGears, 1);
for i = 1:nGears
    if ~isnan(torqueNm(i))
        forceN(i) = torqueNm(i) / (pitchR_mm(i) / 1000);
    else
        torqueNm(i) = 0;
        forceN(i) = 0;
    end
end

fprintf('IDEAL torque & force (frictionless estimate - NOT a measurement, input = %.3g Nm on gear 1):\n', inputTorqueNm);
fprintf('%-6s %12s %12s\n', 'id', 'torque(Nm)', 'force(N)');
for i = 1:nGears
    fprintf('%-6s %12.4f %12.2f\n', mat2str(id{i}), torqueNm(i), forceN(i));
end
fprintf('\n');

%% 5) Precompute real involute tooth outlines (once - geometry doesn't change
%     over time, only each gear's rotation angle does)
PRESSURE_DEG = 20;
outlineX = cell(nGears, 1);
outlineY = cell(nGears, 1);
for i = 1:nGears
    [ox, oy] = involute_gear_outline(teeth(i), pitchR_mm(i), rootR_mm(i), tipR_mm(i), PRESSURE_DEG);
    outlineX{i} = ox;
    outlineY{i} = oy;
end

%% 6) Interactive animated figure: speed slider + play/pause
fig = figure('Name', sprintf('Gear train - %s', imageName), 'NumberTitle', 'off', ...
    'CloseRequestFcn', @onClose);
ax = axes('Parent', fig, 'Position', [0.08 0.18 0.84 0.74]);
axis(ax, 'equal'); hold(ax, 'on'); grid(ax, 'on');
xlabel(ax, 'x (mm)'); ylabel(ax, 'y (mm)');
title(ax, sprintf('%s - %d gear(s)', imageName, nGears));

margin = max(tipR_mm) * 0.3 + 1;
xlim(ax, [min(cx_mm) - max(tipR_mm) - margin, max(cx_mm) + max(tipR_mm) + margin]);
ylim(ax, [min(-cy_mm) - max(tipR_mm) - margin, max(-cy_mm) + max(tipR_mm) + margin]);

colors = lines(nGears);
gearPatch   = cell(nGears, 1);
pitchCircle = cell(nGears, 1);
angle = zeros(nGears, 1);  % current rotation of each gear, radians

for i = 1:nGears
    cx = cx_mm(i); cy = -cy_mm(i);  % flip y: image rows go down, plot y goes up
    gearPatch{i} = patch(ax, 'XData', outlineX{i} + cx, 'YData', outlineY{i} + cy, ...
        'FaceColor', colors(i, :), 'FaceAlpha', 0.55, 'EdgeColor', colors(i, :) * 0.6, ...
        'LineWidth', 1.2);
    th = linspace(0, 2 * pi, 60);
    pitchCircle{i} = plot(ax, cx + pitchR_mm(i) * cos(th), cy + pitchR_mm(i) * sin(th), ...
        '--', 'Color', colors(i, :) * 0.6, 'LineWidth', 0.6);
    plot(ax, cx, cy, '+', 'Color', 'k', 'MarkerSize', 8, 'LineWidth', 1.2);
    text(ax, cx, cy + tipR_mm(i) + margin * 0.25, ...
        sprintf('#%s (%dT)', mat2str(id{i}), teeth(i)), ...
        'HorizontalAlignment', 'center', 'FontSize', 8);
end
legend(ax, 'off');

%% --- UI controls: speed slider + play/pause button -------------------------
SPEED_MIN = -180; SPEED_MAX = 180;  % deg/s range for gear 1, slider-adjustable
speedVal = OMEGA_IN;

uicontrol(fig, 'Style', 'text', 'Units', 'normalized', ...
    'Position', [0.06 0.06 0.20 0.05], 'String', 'Gear 1 speed (deg/s):', ...
    'HorizontalAlignment', 'left');
speedLabel = uicontrol(fig, 'Style', 'text', 'Units', 'normalized', ...
    'Position', [0.80 0.06 0.14 0.05], 'String', sprintf('%.0f deg/s', speedVal), ...
    'HorizontalAlignment', 'left');
speedSlider = uicontrol(fig, 'Style', 'slider', 'Units', 'normalized', ...
    'Position', [0.27 0.065 0.50 0.045], 'Min', SPEED_MIN, 'Max', SPEED_MAX, ...
    'Value', speedVal, 'Callback', @onSliderChange);

playBtn = uicontrol(fig, 'Style', 'togglebutton', 'Units', 'normalized', ...
    'Position', [0.06 0.00 0.20 0.05], 'String', 'Pause', 'Value', 0, ...
    'Callback', @onTogglePlay);

running = true;
lastTime = tic;

animTimer = timer('ExecutionMode', 'fixedRate', 'Period', 0.05, ...
    'TimerFcn', @updateFrame);
start(animTimer);

%% --- Nested callbacks (share this function's workspace) --------------------
    function updateFrame(~, ~)
        if ~running || ~ishandle(fig)
            return
        end
        dt = toc(lastTime);
        lastTime = tic;
        baseSpeed = speedSlider.Value;
        for k = 1:nGears
            % each gear's speed scales with the slider in the same proportion
            % as its speed relative to gear 1's original 60 deg/s base speed
            if OMEGA_IN ~= 0
                gearSpeed = baseSpeed * (omega(k) / OMEGA_IN);
            else
                gearSpeed = 0;
            end
            angle(k) = angle(k) + deg2rad(gearSpeed) * dt;
        end
        for k = 1:nGears
            cx = cx_mm(k); cy = -cy_mm(k);
            c = cos(angle(k)); s = sin(angle(k));
            xr = c * outlineX{k} - s * outlineY{k};
            yr = s * outlineX{k} + c * outlineY{k};
            set(gearPatch{k}, 'XData', xr + cx, 'YData', yr + cy);
        end
        drawnow limitrate;
    end

    function onSliderChange(src, ~)
        speedLabel.String = sprintf('%.0f deg/s', src.Value);
    end

    function onTogglePlay(src, ~)
        running = ~src.Value;  % Value=1 means pressed/held -> paused
        if running
            src.String = 'Pause';
            lastTime = tic;  % avoid a big dt jump after resuming
        else
            src.String = 'Play';
        end
    end

    function onClose(~, ~)
        if exist('animTimer', 'var') && isvalid(animTimer)
            stop(animTimer);
            delete(animTimer);
        end
        delete(fig);
    end

end


function [xAll, yAll] = involute_gear_outline(nTeeth, pitchR, rootR, tipR, pressureDeg)
%INVOLUTE_GEAR_OUTLINE  Closed polygon (x,y) outline of one gear, centered at
%the origin with tooth 1 centered on angle 0, using the real involute-of-a-
%circle tooth-flank curve. Returns NaN-free column vectors tracing the full
%outline once around (first point == last point).
%
% Geometry (standard gear-design formulas):
%   baseR  = pitchR * cos(pressureAngle)
%   On the involute, a point at radius r has local pressure angle
%     alpha(r) = acos(baseR / r)
%   and its angular position (swept from where the involute leaves the base
%   circle) is given by the involute function:
%     inv(alpha) = tan(alpha) - alpha
%   The flank is aligned so the tooth has half-angle halfToothAngle AT THE
%   PITCH CIRCLE (tooth width = space width there, i.e. a 50/50 split of the
%   angular pitch - gear_inspector.py has no way to measure actual tooth
%   thickness from a photo, so this is the standard assumed default):
%     theta(r) = halfToothAngle - (inv(alpha(r)) - inv(alpha(pitchR)))
%   This makes the tooth WIDEST at the root and NARROWEST at the tip, which
%   matches how real involute teeth taper (verified numerically before this
%   was translated into MATLAB).
%
% Below the base circle (only when baseR > rootR, common for low tooth
% counts), the flank is simplified to a straight radial line down to the
% root circle - real gears have a curved fillet there instead, cut by the
% manufacturing process, which this does not attempt to reproduce.

if nargin < 5 || isempty(pressureDeg)
    pressureDeg = 20;
end

% Guard against degenerate inputs (keeps the animation from erroring out on
% a noisy/unusual measurement rather than stopping the whole simulation)
if ~(tipR > rootR) || nTeeth < 4
    th = linspace(0, 2 * pi, 60);
    xAll = tipR * cos(th);
    yAll = tipR * sin(th);
    return
end

phi = deg2rad(pressureDeg);
baseR = pitchR * cos(phi);
angularPitch = 2 * pi / nTeeth;
halfToothAngle = angularPitch / 4;
invP = tan(phi) - phi;

rStart = max(baseR, rootR);
rStart = min(rStart, tipR * 0.999);
nSamp = 14;
r = linspace(rStart, tipR, nSamp);
alpha = acos(min(1, baseR ./ r));
invA = tan(alpha) - alpha;
thetaUpper = halfToothAngle - (invA - invP);
thetaUpper = max(thetaUpper, 0);

if baseR > rootR
    r = [rootR, r];
    thetaUpper = [thetaUpper(1), thetaUpper];
end

% One tooth, traced in monotonically increasing angle order: lower flank
% root->tip, then upper flank tip->root. This ordering is what guarantees a
% simple (non-self-intersecting) polygon once replicated around the gear.
rFull = [r, fliplr(r)];
thetaFull = [-thetaUpper, fliplr(thetaUpper)];
xTooth = rFull .* cos(thetaFull);
yTooth = rFull .* sin(thetaFull);

xAll = [];
yAll = [];
arcPts = 5;
for k = 0:nTeeth - 1
    rot = k * angularPitch;
    c = cos(rot); s = sin(rot);
    xk = c * xTooth - s * yTooth;
    yk = s * xTooth + c * yTooth;
    xAll = [xAll, xk]; %#ok<AGROW>
    yAll = [yAll, yk]; %#ok<AGROW>
    if rootR > 1e-9
        a0 = rot + thetaUpper(1);
        a1 = rot + angularPitch - thetaUpper(1);
        arcAngles = linspace(a0, a1, arcPts);
        xAll = [xAll, rootR * cos(arcAngles)]; %#ok<AGROW>
        yAll = [yAll, rootR * sin(arcAngles)]; %#ok<AGROW>
    end
end
% close the loop explicitly
xAll(end + 1) = xAll(1);
yAll(end + 1) = yAll(1);
end
