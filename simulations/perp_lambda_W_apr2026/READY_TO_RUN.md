# Perpendicular B-field λ/W Campaign — READY TO RUN
## Referee Concern #4: Direct λ/W measurements for perpendicular-field configurations

**Prepared by**: ASTRA-PA, 30 April 2026  
**Status**: ⏳ Waiting for astra-climate to come online  
**Estimated wall time**: ~2–3 hours (9 concurrent × ~20 min/sim for FRAG sims)

---

## Part 1: Bringing astra-climate Back Online

astra-climate is a Google Compute Engine (GCE) `n2d-highcpu-224` instance (224 vCPUs, 224 GB RAM).
Its SSH is currently unreachable, most likely because the instance was stopped (not deleted) after
the April 29 campaigns completed to save costs.

### Step-by-step GCE restart

1. **Open the GCE Console**  
   Go to: https://console.cloud.google.com/compute/instances  
   Sign in with the Google account that owns the ASTRA project.

2. **Find the instance**  
   Look for an instance named something like `astra-climate` or `astra-highcpu`.  
   Its status will show **TERMINATED** (stopped) or **RUNNING** (if it started automatically).

3. **Start the instance**  
   Click the three-dot menu → **Start / Resume**.  
   The instance takes 2–3 minutes to boot.

4. **Note the external IP**  
   The static IP is `34.143.130.135`. If the IP shown differs, update  
   `/shared/keys/astra-climate-ssh.env` and `SHARED.md` with the new IP.

5. **Test SSH connectivity** (from your Taurus agent terminal):
   ```bash
   ssh -i /shared/keys/astra-climate.key \
       -o StrictHostKeyChecking=accept-new \
       -o ConnectTimeout=15 \
       fetch-agi@34.143.130.135 "echo 'astra-climate online'"
   ```
   You should see: `astra-climate online`

6. **Check disk space**:
   ```bash
   ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 "df -h /data && df -h /"
   ```
   The `/data` SSD mount needs at least **~30 GB free** for this campaign.  
   After the April 29 campaigns, 54.9 GB was used out of 527 GB — so ~470 GB free.  
   If `/data` isn't mounted, run: `sudo mount /dev/sdb /data`

7. **Verify the Athena++ binary**:
   ```bash
   ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
     "/home/fetch-agi/athena/bin/athena --help 2>&1 | head -5"
   ```

8. **Start the Ray cluster**:
   ```bash
   ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
     "ray start --head --num-cpus=224 --object-store-memory=50000000000 &"
   ```
   Wait 10 seconds, then verify:
   ```bash
   ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
     "ray status"
   ```
   Expected: `1 node(s) with resources: CPU: 224.0`

---

## Part 2: Deploying the Campaign Files

Copy the campaign scripts to astra-climate:

```bash
scp -i /shared/keys/astra-climate.key \
    /shared/ASTRA/simulations/perp_lambda_W_apr2026/perp_lambda_W_runner.py \
    fetch-agi@34.143.130.135:/home/fetch-agi/perp_lambda_W_runner.py

scp -i /shared/keys/astra-climate.key \
    /shared/ASTRA/simulations/perp_lambda_W_apr2026/analyse_perp_lambda_W.py \
    fetch-agi@34.143.130.135:/home/fetch-agi/analyse_perp_lambda_W.py
```

Create the output directory:
```bash
ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
    "mkdir -p /data/perp_lambda_W_runs"
```

---

## Part 3: Running the Campaign

### Option A — Interactive (recommended for first time)

```bash
ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135
screen -S perp_lw                   # or tmux new -s perp_lw
cd /home/fetch-agi
python3 perp_lambda_W_runner.py
```

Press `Ctrl+A, D` (screen) or `Ctrl+B, D` (tmux) to detach.  
Reattach later with: `screen -r perp_lw` or `tmux attach -t perp_lw`

### Option B — Detached nohup

```bash
ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
    "nohup python3 /home/fetch-agi/perp_lambda_W_runner.py \
     > /data/perp_lambda_W_runs/runner_stdout.log 2>&1 &"
```

Monitor progress:
```bash
ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
    "tail -f /data/perp_lambda_W_runs/campaign.log"
```

---

## Part 4: Monitoring

Check progress at any time:
```bash
# How many sims done?
ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
    "cat /data/perp_lambda_W_runs/results.json | python3 -c \
     'import json,sys; d=json.load(sys.stdin); \
      print(len(d), \"done\"); \
      [print(r[\"sim_id\"], r[\"outcome\"], r.get(\"t_frag\",\"N/A\")) for r in d]'"

# Disk usage
ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
    "du -sh /data/perp_lambda_W_runs/"

# Live log tail
ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
    "tail -30 /data/perp_lambda_W_runs/campaign.log"

# Count HDF5 snapshots (confirms λ/W data is being written)
ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
    "find /data/perp_lambda_W_runs -name '*.athdf' | wc -l"
```

**Expected**: ~20–30 HDF5 snapshots per sim (DT_HDF5=0.05 t_J, tlim=2.0 t_J).  
A sim that fragments at t=0.5 t_J will produce ~10 snapshots.

---

## Part 5: Running the λ/W Analysis

Once the campaign.log shows "CAMPAIGN COMPLETE":

```bash
ssh -i /shared/keys/astra-climate.key fetch-agi@34.143.130.135 \
    "cd /home/fetch-agi && pip3 install h5py scipy matplotlib -q && \
     python3 analyse_perp_lambda_W.py"
```

This will:
1. Read all `.athdf` snapshots from each simulation
2. Compute axial density profiles at each snapshot time
3. Measure σ/μ (axial contrast) — the key metric for λ/W detectability
4. If axial contrast > 5%: measure λ/W via peak-finding + Fourier analysis
5. Otherwise: report "radial collapse dominant" as a definitive negative result
6. Generate figures A and B in `/data/perp_lambda_W_runs/figures/`
7. Write `lambda_W_analysis.json`

---

## Part 6: Collecting Results

After analysis completes, fetch everything:

```bash
# Pull analysis JSON
scp -i /shared/keys/astra-climate.key \
    "fetch-agi@34.143.130.135:/data/perp_lambda_W_runs/lambda_W_analysis.json" \
    /workspace/perp_lambda_W_results/

# Pull figures
scp -r -i /shared/keys/astra-climate.key \
    "fetch-agi@34.143.130.135:/data/perp_lambda_W_runs/figures/" \
    /workspace/perp_lambda_W_results/

# Pull campaign log and results.json
scp -i /shared/keys/astra-climate.key \
    "fetch-agi@34.143.130.135:/data/perp_lambda_W_runs/campaign.log" \
    "fetch-agi@34.143.130.135:/data/perp_lambda_W_runs/results.json" \
    /workspace/perp_lambda_W_results/
```

Then notify ASTRA-PA to package and push to GitHub.

---

## Campaign Specification

| Parameter | Value |
|-----------|-------|
| f values | 2.0, 2.5, 3.0 |
| β values | 0.3, 1.0 |
| M values | 1.0, 2.0 |
| Seeds | 42, 43 |
| θ (B-field) | 90° (perpendicular) |
| Total sims | **24** |
| Domain | 256×64×64 cells (8×2×2 λ_J) |
| Resolution | 32 cells/λ_J |
| MeshBlock | 64×32×32 → np=16/sim |
| Concurrent | 9 sims × 16 = 144 cores |
| tlim | 2.0 t_J |
| HDF5 interval | **0.05 t_J** (critical!) |
| HST interval | 0.005 t_J |
| Wall-clock limit | 6 hours/sim |
| Est. total wall | 2–3 hours |

---

## What to Expect

Based on previous perpendicular-B results (PERP_LAMBDA_V1, April 2026):
- All 24 sims will likely FRAG, with t_frag = 0.375–0.641 t_J
- **Critical question**: does axial beading develop before radial collapse?
- Previous λ/W estimates for perp-B sims gave ~14 (unreliable x1 peak-finding)
- This campaign uses proper σ/μ gating to distinguish real axial structure from noise

**If λ/W is unmeasurable** (most likely outcome): the analysis reports this quantitatively
as `axial_contrast_max < 0.05`, which is itself a definitive answer to the referee — confirming
that perpendicular B configurations undergo radial collapse before axial beading develops,
and therefore λ/W cannot be measured for this field geometry. This closes the question.

**If λ/W is measurable** (less likely, would occur if near-critical sims develop beading):
the λ/W values and figures will be extracted and reported.

Either way, this campaign provides the definitive, quantitative answer the referee asked for.

---

## Files in This Package

| File | Description |
|------|-------------|
| `perp_lambda_W_runner.py` | Ray-based campaign runner (24 sims) |
| `analyse_perp_lambda_W.py` | λ/W analysis with axial contrast gating |
| `READY_TO_RUN.md` | This file — step-by-step instructions |
