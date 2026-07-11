#!/usr/bin/env python3
"""
ASTRA Astronomical Discovery Testing Suite
============================================

Comprehensive testing for genuine astronomical discovery capabilities.

Tests:
1. Autonomous system initialization
2. ASTRA core connection
3. Discovery quality and novelty
4. Validation pipeline functionality
5. Persistent storage
6. Discovery diversity
7. Scientific relevance

Version: 1.0.0
Date: 2026-07-01
"""

import sys
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import tempfile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AstronomicalDiscoveryTester:
    """Comprehensive tester for astronomical discovery capabilities"""

    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.astra_system = None
        self.discovery_system = None

    def record_result(self, test_name: str, passed: bool, details: str = ""):
        """Record a test result"""
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"  Details: {details}")

    def test_1_dependencies(self) -> bool:
        """Test 1: Check if all required dependencies are available"""
        logger.info("Test 1: Checking dependencies...")

        required_modules = [
            ('astra_core', 'ASTRA core system'),
            ('astra_core.scientific_discovery', 'Scientific discovery module'),
            ('astra_core.domains', 'Astronomical domains'),
        ]

        all_available = True
        missing = []

        for module, description in required_modules:
            try:
                __import__(module)
                logger.info(f"  ✅ {description} available")
            except ImportError:
                logger.warning(f"  ❌ {description} missing")
                missing.append(description)
                all_available = False

        details = f"All dependencies available" if all_available else f"Missing: {', '.join(missing)}"
        self.record_result("Dependencies Check", all_available, details)
        return all_available

    def test_2_domain_registration(self) -> bool:
        """Test 2: Verify astronomical domains are properly registered"""
        logger.info("Test 2: Checking astronomical domain registration...")

        try:
            from astra_core.domains.registry import DomainRegistry

            registry = DomainRegistry()
            domains = registry.list_domains()

            # Essential astronomical domains
            essential_domains = [
                'exoplanets', 'cosmology', 'gravitational_waves',
                'ism', 'star_formation', 'solar_system'
            ]

            registered_essential = [d for d in essential_domains if d in domains]

            details = f"Registered {len(domains)} domains, {len(registered_essential)}/{len(essential_domains)} essential"
            passed = len(registered_essential) >= 4  # At least 4 essential domains

            self.record_result("Domain Registration", passed, details)
            return passed

        except Exception as e:
            details = f"Domain registration failed: {str(e)}"
            self.record_result("Domain Registration", False, details)
            return False

    def test_3_astra_system_creation(self) -> bool:
        """Test 3: Create and connect ASTRA system"""
        logger.info("Test 3: Creating ASTRA core system...")

        try:
            from astra_core import create_stan_system

            logger.info("  Creating ASTRA system...")
            self.astra_system = create_stan_system()

            if self.astra_system is None:
                details = "ASTRA system creation returned None"
                self.record_result("ASTRA System Creation", False, details)
                return False

            # Test basic functionality
            logger.info("  Testing basic query capability...")
            test_result = self.astra_system.answer("What is a black hole?")

            if test_result and 'answer' in test_result:
                details = f"ASTRA system created and functional, response length: {len(test_result.get('answer', ''))}"
                self.record_result("ASTRA System Creation", True, details)
                return True
            else:
                details = "ASTRA system created but query failed"
                self.record_result("ASTRA System Creation", False, details)
                return False

        except Exception as e:
            details = f"ASTRA system creation failed: {str(e)}"
            self.record_result("ASTRA System Creation", False, details)
            return False

    def test_4_discovery_system_init(self) -> bool:
        """Test 4: Initialize discovery system with ASTRA connection"""
        logger.info("Test 4: Initializing discovery system...")

        try:
            from astra_core.autonomous_startup_discovery_v2 import (
                GenuineDiscoverySystem,
                GenuineDiscoveryConfig
            )

            logger.info("  Creating discovery system...")
            config = GenuineDiscoveryConfig(
                discovery_interval_seconds=10,  # Fast for testing
                minimum_novelty_score=0.3,
                minimum_probability=0.4,
                enable_data_archive_analysis=True,
                enable_literature_mining=True
            )

            self.discovery_system = GenuineDiscoverySystem(config=config)

            # Connect ASTRA system
            if self.astra_system:
                logger.info("  Connecting ASTRA system to discovery...")
                self.discovery_system.initialize_with_astra(self.astra_system)

            # Verify connection
            has_astra = self.discovery_system.astra_system is not None

            details = f"Discovery system created, ASTRA connected: {has_astra}"
            passed = has_astra

            self.record_result("Discovery System Initialization", passed, details)
            return passed

        except Exception as e:
            details = f"Discovery system initialization failed: {str(e)}"
            self.record_result("Discovery System Initialization", False, details)
            return False

    def test_5_discovery_generation(self) -> bool:
        """Test 5: Generate astronomical discoveries"""
        logger.info("Test 5: Testing discovery generation...")

        if not self.discovery_system:
            logger.error("  Discovery system not available")
            self.record_result("Discovery Generation", False, "Discovery system not initialized")
            return False

        try:
            logger.info("  Running discovery cycle...")
            # Run a single discovery cycle
            discoveries = self.discovery_system.run_single_discovery_cycle()

            if not discoveries:
                details = "No discoveries generated"
                self.record_result("Discovery Generation", False, details)
                return False

            logger.info(f"  Generated {len(discoveries)} discovery candidates")

            # Check discovery quality
            valid_discoveries = []
            for discovery in discoveries:
                # Check if discovery has required fields
                if 'title' in discovery and 'description' in discovery:
                    # Check if it's not just basic knowledge
                    title = discovery['title']
                    desc = discovery['description']

                    # Skip obviously basic knowledge
                    basic_phrases = ['studies planets orbiting stars', 'is the study of', 'are objects that']
                    is_basic = any(phrase in title.lower() or phrase in desc.lower() for phrase in basic_phrases)

                    if not is_basic and len(desc) > 50:  # Substantial content
                        valid_discoveries.append(discovery)

            details = f"Generated {len(discoveries)} candidates, {len(valid_discoveries)} valid discoveries"
            passed = len(valid_discoveries) > 0

            self.record_result("Discovery Generation", passed, details)
            return passed

        except Exception as e:
            details = f"Discovery generation failed: {str(e)}"
            self.record_result("Discovery Generation", False, details)
            return False

    def test_6_validation_pipeline(self) -> bool:
        """Test 6: Test validation pipeline functionality"""
        logger.info("Test 6: Testing validation pipeline...")

        if not self.discovery_system:
            logger.error("  Discovery system not available")
            self.record_result("Validation Pipeline", False, "Discovery system not initialized")
            return False

        try:
            # Check if validation pipeline exists
            has_pipeline = self.discovery_system.validation_pipeline is not None

            if not has_pipeline:
                details = "Validation pipeline not initialized"
                self.record_result("Validation Pipeline", False, details)
                return False

            logger.info("  Testing validation with sample discovery...")

            # Create a test discovery
            test_discovery = {
                'title': 'Test Discovery: Magnetic Reconnection in Solar Flares',
                'description': 'Analysis of solar flare data reveals unexpected patterns in magnetic reconnection events that suggest new acceleration mechanisms.',
                'domain': 'solar_physics',
                'novelty_score': 0.8,
                'confidence': 0.7
            }

            # Try to validate it
            validation_result = self.discovery_system.validate_discovery(test_discovery)

            if validation_result:
                details = f"Validation pipeline functional, result: {validation_result.get('status', 'unknown')}"
                passed = True
            else:
                details = "Validation pipeline returned None"
                passed = False

            self.record_result("Validation Pipeline", passed, details)
            return passed

        except Exception as e:
            details = f"Validation pipeline test failed: {str(e)}"
            self.record_result("Validation Pipeline", False, details)
            return False

    def test_7_discovery_diversity(self) -> bool:
        """Test 7: Test discovery diversity across domains"""
        logger.info("Test 7: Testing discovery diversity...")

        if not self.discovery_system:
            logger.error("  Discovery system not available")
            self.record_result("Discovery Diversity", False, "Discovery system not initialized")
            return False

        try:
            logger.info("  Running multiple discovery cycles...")

            discoveries_by_domain = {}
            cycles_to_run = 5

            for i in range(cycles_to_run):
                logger.info(f"  Running cycle {i+1}/{cycles_to_run}...")
                discoveries = self.discovery_system.run_single_discovery_cycle()

                for discovery in discoveries:
                    domain = discovery.get('domain', 'unknown')
                    if domain not in discoveries_by_domain:
                        discoveries_by_domain[domain] = 0
                    discoveries_by_domain[domain] += 1

                time.sleep(1)  # Small delay between cycles

            unique_domains = len(discoveries_by_domain)
            total_discoveries = sum(discoveries_by_domain.values())

            details = f"Generated {total_discoveries} discoveries across {unique_domains} domains: {list(discoveries_by_domain.keys())}"
            passed = unique_domains >= 2  # At least 2 different domains

            self.record_result("Discovery Diversity", passed, details)
            return passed

        except Exception as e:
            details = f"Discovery diversity test failed: {str(e)}"
            self.record_result("Discovery Diversity", False, details)
            return False

    def test_8_scientific_relevance(self) -> bool:
        """Test 8: Evaluate scientific relevance of discoveries"""
        logger.info("Test 8: Testing scientific relevance...")

        if not self.discovery_system:
            logger.error("  Discovery system not available")
            self.record_result("Scientific Relevance", False, "Discovery system not initialized")
            return False

        try:
            logger.info("  Generating discoveries for relevance assessment...")

            discoveries = self.discovery_system.run_single_discovery_cycle()

            # Check for scientific relevance indicators
            relevant_count = 0
            total_count = len(discoveries)

            for discovery in discoveries:
                title = discovery.get('title', '').lower()
                desc = discovery.get('description', '').lower()

                # Scientific relevance indicators
                scientific_terms = [
                    'analysis', 'measurement', 'observation', 'detection',
                    'correlation', 'pattern', 'relationship', 'mechanism',
                    'process', 'evolution', 'formation', 'structure'
                ]

                has_scientific_content = any(term in title or term in desc for term in scientific_terms)
                has_technical_detail = len(desc) > 100  # Substantial technical content

                if has_scientific_content and has_technical_detail:
                    relevant_count += 1

            if total_count > 0:
                relevance_rate = relevant_count / total_count
            else:
                relevance_rate = 0

            details = f"{relevant_count}/{total_count} discoveries scientifically relevant ({relevance_rate:.1%})"
            passed = relevance_rate >= 0.3  # At least 30% relevance rate

            self.record_result("Scientific Relevance", passed, details)
            return passed

        except Exception as e:
            details = f"Scientific relevance test failed: {str(e)}"
            self.record_result("Scientific Relevance", False, details)
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive report"""
        logger.info("=" * 60)
        logger.info("ASTRA Astronomical Discovery Testing Suite")
        logger.info("=" * 60)

        # Run all tests
        tests = [
            self.test_1_dependencies,
            self.test_2_domain_registration,
            self.test_3_astra_system_creation,
            self.test_4_discovery_system_init,
            self.test_5_discovery_generation,
            self.test_6_validation_pipeline,
            self.test_7_discovery_diversity,
            self.test_8_scientific_relevance
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                logger.error(f"Test {test.__name__} crashed: {e}")
                self.record_result(f"{test.__name__} (CRASH)", False, f"Test crashed: {str(e)}")

        # Generate report
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        failed_tests = total_tests - passed_tests

        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'duration_seconds': duration,
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            'test_results': self.test_results
        }

        # Print summary
        logger.info("=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {report['summary']['success_rate']:.1%}")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info("=" * 60)

        return report

def main():
    """Main test execution"""
    tester = AstronomicalDiscoveryTester()
    report = tester.run_all_tests()

    # Save report to file
    report_file = Path('/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/astronomical_discovery_test_report.json')
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Test report saved to: {report_file}")

    # Exit with appropriate code
    sys.exit(0 if report['summary']['failed'] == 0 else 1)

if __name__ == '__main__':
    main()