#!/usr/bin/env python3
"""
Monitor simulation progress and detect issues.

This script tracks the status of running simulations, generates progress reports,
and identifies problematic simulations that may need intervention.
"""

import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


def check_simulation_status(output_dir: str) -> str:
    """
    Check if simulation has completed, failed, or is still running.

    Parameters
    ----------
    output_dir : str
        Simulation output directory

    Returns
    -------
    str
        Status: 'completed', 'running', 'failed', 'not_started', or 'timeout'
    """
    output_path = Path(output_dir)

    # Check for final output file
    final_files = list(output_path.glob("*.final.out")) + list(output_path.glob("*/*.h5"))

    # Check for log file
    log_files = list(output_path.glob("*.log"))

    if final_files:
        # Has final output - check if complete
        # (This is a simplified check; actual implementation may vary)
        return 'completed'

    elif log_files:
        # Has log file - check for errors
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    content = f.read()

                    if 'ERROR' in content or 'FATAL' in content or 'ABORT' in content:
                        return 'failed'
                    elif 'SIGTERM' in content or 'killed' in content:
                        return 'timeout'
                    elif 'Tlim is reached' in content:
                        return 'completed'

                # Check modification time - if recent, likely still running
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if datetime.now() - mtime < timedelta(minutes=5):
                    return 'running'
                else:
                    # Log file exists but old - might be stalled
                    return 'stalled'

            except Exception:
                pass

        return 'running'

    else:
        # No outputs at all
        return 'not_started'


def get_simulation_info(config_file: str) -> Dict[str, Any]:
    """
    Extract simulation parameters from config file.

    Parameters
    ----------
    config_file : str
        Path to config JSON file

    Returns
    -------
    dict
        Simulation parameters
    """
    try:
        with open(config_file) as f:
            config = json.load(f)

        return config.get('metadata', {})

    except Exception:
        return {}


def scan_campaign(
    campaign_name: str,
    config_base_dir: str = 'peer_review_simulation_configs',
    output_base_dir: str = 'outputs'
) -> Dict[str, Dict[str, Any]]:
    """
    Scan all simulations in a campaign and check their status.

    Parameters
    ----------
    campaign_name : str
        Campaign identifier
    config_base_dir : str
        Base directory for config files
    output_base_dir : str
        Base directory for simulation outputs

    Returns
    -------
    dict
        Status information for each simulation
    """
    statuses = {}

    # Find config files for this campaign
    config_dir = Path(config_base_dir) / campaign_name.lower()

    if not config_dir.exists():
        # Try subdirectories
        config_base = Path(config_base_dir)
        for subdir in config_base.iterdir():
            if campaign_name.lower() in subdir.name.lower():
                config_dir = subdir
                break

    if not config_dir.exists():
        return {'error': f'Config directory not found for campaign: {campaign_name}'}

    config_files = list(config_dir.rglob('*.json'))

    for config_file in config_files:
        # Extract simulation info
        sim_info = get_simulation_info(str(config_file))

        # Determine output directory
        sim_name = sim_info.get('campaign', 'unknown') + '_' + config_file.stem
        output_dir = Path(output_base_dir) / sim_info.get('campaign', campaign_name) / sim_name

        # Check status
        status = check_simulation_status(str(output_dir))

        statuses[config_file.stem] = {
            'config_file': str(config_file),
            'output_dir': str(output_dir),
            'status': status,
            'parameters': sim_info
        }

    return statuses


def generate_html_report(
    campaign_name: str,
    statuses: Dict[str, Dict[str, Any]],
    output_file: Optional[str] = None
) -> str:
    """
    Generate HTML progress report for campaign.

    Parameters
    ----------
    campaign_name : str
        Campaign identifier
    statuses : dict
        Simulation status information
    output_file : str, optional
        Output HTML file path

    Returns
    -------
    str
        HTML content
    """
    # Count statistics
    total = len(statuses)
    completed = sum(1 for s in statuses.values() if s.get('status') == 'completed')
    running = sum(1 for s in statuses.values() if s.get('status') == 'running')
    failed = sum(1 for s in statuses.values() if s.get('status') == 'failed')
    stalled = sum(1 for s in statuses.values() if s.get('status') == 'stalled')
    not_started = sum(1 for s in statuses.values() if s.get('status') == 'not_started')

    # Status colors
    colors = {
        'completed': '#4CAF50',  # Green
        'running': '#2196F3',    # Blue
        'failed': '#F44336',     # Red
        'stalled': '#FF9800',    # Orange
        'not_started': '#9E9E9E'  # Gray
    }

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{campaign_name} Progress Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .stat-box {{ padding: 15px; border-radius: 5px; text-align: center; min-width: 100px; }}
        .stat-box.completed {{ background-color: #E8F5E9; }}
        .stat-box.running {{ background-color: #E3F2FD; }}
        .stat-box.failed {{ background-color: #FFEBEE; }}
        .stat-box.stalled {{ background-color: #FFF3E0; }}
        .stat-box.not_started {{ background-color: #F5F5F5; }}
        .stat-number {{ font-size: 32px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; color: #666; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status-completed {{ color: #4CAF50; font-weight: bold; }}
        .status-running {{ color: #2196F3; font-weight: bold; }}
        .status-failed {{ color: #F44336; font-weight: bold; }}
        .status-stalled {{ color: #FF9800; font-weight: bold; }}
        .status-not_started {{ color: #9E9E9E; }}
        .timestamp {{ font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <h1>{campaign_name} Campaign Progress</h1>
    <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <div class="stat-box completed">
            <div class="stat-number">{completed}</div>
            <div class="stat-label">Completed ({completed/total*100:.1f}%)</div>
        </div>
        <div class="stat-box running">
            <div class="stat-number">{running}</div>
            <div class="stat-label">Running ({running/total*100:.1f}%)</div>
        </div>
        <div class="stat-box failed">
            <div class="stat-number">{failed}</div>
            <div class="stat-label">Failed ({failed/total*100:.1f}%)</div>
        </div>
        <div class="stat-box stalled">
            <div class="stat-number">{stalled}</div>
            <div class="stat-label">Stalled ({stalled/total*100:.1f}%)</div>
        </div>
        <div class="stat-box not_started">
            <div class="stat-number">{not_started}</div>
            <div class="stat-label">Not Started ({not_started/total*100:.1f}%)</div>
        </div>
    </div>

    <h2>Simulation Details</h2>
    <table>
        <tr>
            <th>Config ID</th>
            <th>f</th>
            <th>β</th>
            <th>M</th>
            <th>θ</th>
            <th>Seed</th>
            <th>Status</th>
        </tr>
"""

    # Sort by status (completed first) then by config ID
    sorted_configs = sorted(
        statuses.items(),
        key=lambda x: (
            x[1].get('status', 'not_started') != 'completed',
            x[1].get('status', 'not_started'),
            x[0]
        )
    )

    for config_id, info in sorted_configs:
        params = info.get('parameters', {})
        status = info.get('status', 'unknown')

        html += f"""
        <tr>
            <td>{config_id}</td>
            <td>{params.get('f', 'N/A')}</td>
            <td>{params.get('beta', 'N/A')}</td>
            <td>{params.get('M', 'N/A')}</td>
            <td>{params.get('theta', 'N/A')}</td>
            <td>{params.get('seed', 'N/A')}</td>
            <td class="status-{status}">{status.replace('_', ' ').title()}</td>
        </tr>
"""

    html += """
    </table>
</body>
</html>
"""

    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(html)
        print(f"HTML report saved to: {output_file}")

    return html


def generate_text_report(
    campaign_name: str,
    statuses: Dict[str, Dict[str, Any]]
) -> str:
    """
    Generate text progress report for campaign.

    Parameters
    ----------
    campaign_name : str
        Campaign identifier
    statuses : dict
        Simulation status information

    Returns
    -------
    str
        Text report
    """
    total = len(statuses)
    completed = sum(1 for s in statuses.values() if s.get('status') == 'completed')
    running = sum(1 for s in statuses.values() if s.get('status') == 'running')
    failed = sum(1 for s in statuses.values() if s.get('status') == 'failed')

    report = f"""
{'='*70}
{campaign_name} Campaign Progress Report
{'='*70}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY
-------
Total simulations:    {total}
Completed:           {completed} ({completed/total*100:.1f}%)
Running:             {running} ({running/total*100:.1f}%)
Failed:              {failed} ({failed/total*100:.1f}%)

"""

    # List failed simulations
    if failed > 0:
        report += "\nFAILED SIMULATIONS\n"
        report += "-"*70 + "\n"
        for config_id, info in statuses.items():
            if info.get('status') == 'failed':
                params = info.get('parameters', {})
                report += f"  {config_id}: f={params.get('f', 'N/A')}, "
                report += f"β={params.get('beta', 'N/A')}, M={params.get('M', 'N/A')}\n"

    # List stalled simulations
    stalled = sum(1 for s in statuses.values() if s.get('status') == 'stalled')
    if stalled > 0:
        report += "\nSTALLED SIMULATIONS (may need intervention)\n"
        report += "-"*70 + "\n"
        for config_id, info in statuses.items():
            if info.get('status') == 'stalled':
                params = info.get('parameters', {})
                report += f"  {config_id}: f={params.get('f', 'N/A')}, "
                report += f"β={params.get('beta', 'N/A')}, M={params.get('M', 'N/A')}\n"

    report += f"\n{'='*70}\n"

    return report


def continuous_monitor(
    campaign_name: str,
    interval_seconds: int = 300,
    max_duration_hours: float = 24.0
):
    """
    Continuously monitor campaign progress and update reports.

    Parameters
    ----------
    campaign_name : str
        Campaign identifier
    interval_seconds : int
        Update interval in seconds
    max_duration_hours : float
        Maximum monitoring duration
    """
    start_time = time.time()
    max_seconds = max_duration_hours * 3600

    print(f"Starting continuous monitor for {campaign_name}")
    print(f"Update interval: {interval_seconds}s")
    print(f"Max duration: {max_duration_hours}h")
    print()

    while time.time() - start_time < max_seconds:
        # Scan campaign
        statuses = scan_campaign(campaign_name)

        # Generate reports
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = f"progress_{campaign_name}_{timestamp}.html"
        text_file = f"progress_{campaign_name}_{timestamp}.txt"

        generate_html_report(campaign_name, statuses, html_file)
        text_report = generate_text_report(campaign_name, statuses)

        with open(text_file, 'w') as f:
            f.write(text_report)

        print(text_report)

        # Check if all done
        all_done = all(
            s.get('status') in ['completed', 'failed']
            for s in statuses.values()
        )

        if all_done:
            print("\nAll simulations completed!")
            break

        # Wait for next update
        wait_time = min(interval_seconds, max_seconds - (time.time() - start_time))
        if wait_time > 0:
            print(f"Next update in {wait_time}s...")
            time.sleep(wait_time)


def main():
    """Command-line interface for progress monitoring."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Monitor peer review response campaign progress'
    )
    parser.add_argument(
        'campaign',
        help='Campaign name (e.g., SUPERCRITICAL_LONG)'
    )
    parser.add_argument(
        '--config-dir',
        help='Base directory for config files',
        default='peer_review_simulation_configs'
    )
    parser.add_argument(
        '--output-dir',
        help='Base directory for simulation outputs',
        default='outputs'
    )
    parser.add_argument(
        '--html',
        help='Generate HTML report',
        action='store_true'
    )
    parser.add_argument(
        '--continuous',
        help='Continuous monitoring mode',
        action='store_true'
    )
    parser.add_argument(
        '--interval',
        help='Update interval for continuous mode (seconds)',
        type=int,
        default=300
    )
    parser.add_argument(
        '--max-duration',
        help='Maximum monitoring duration (hours)',
        type=float,
        default=24.0
    )

    args = parser.parse_args()

    if args.continuous:
        continuous_monitor(
            args.campaign,
            interval_seconds=args.interval,
            max_duration_hours=args.max_duration
        )
    else:
        # Single scan
        statuses = scan_campaign(
            args.campaign,
            config_base_dir=args.config_dir,
            output_base_dir=args.output_dir
        )

        if args.html:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            html_file = f"progress_{args.campaign}_{timestamp}.html"
            generate_html_report(args.campaign, statuses, html_file)

        text_report = generate_text_report(args.campaign, statuses)
        print(text_report)


if __name__ == '__main__':
    main()
