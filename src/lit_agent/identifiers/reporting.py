"""Comprehensive reporting and visualization for validation assessment."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from .base import IdentifierExtractionResult, AcademicIdentifier, IdentifierType

logger = logging.getLogger(__name__)


class ValidationReporter:
    """Generate comprehensive validation reports with statistics and visualizations."""

    def __init__(self, output_dir: str = "reports"):
        """Initialize the validation reporter.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_validation_report(
        self,
        results: List[IdentifierExtractionResult],
        report_name: Optional[str] = None,
        include_detailed_papers: bool = True,
    ) -> Dict[str, Any]:
        """Generate comprehensive validation assessment report.

        Args:
            results: List of extraction results to analyze
            report_name: Custom name for the report
            include_detailed_papers: Whether to include detailed paper listings

        Returns:
            Dictionary containing the complete report data
        """
        if not report_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"validation_assessment_{timestamp}"

        logger.info(f"Generating validation report: {report_name}")

        # Collect all identifiers from all results
        all_identifiers = []
        for result in results:
            all_identifiers.extend(result.identifiers)

        # Generate comprehensive statistics
        stats = self._generate_comprehensive_stats(results, all_identifiers)

        # Generate validation analysis
        validation_analysis = self._analyze_validation_performance(all_identifiers)

        # Generate stratified performance analysis
        stratified_analysis = self._analyze_stratified_performance(
            all_identifiers, [url for result in results for url in result.failed_urls]
        )

        # Generate failure analysis
        failure_analysis = self._generate_failure_analysis(results)

        # Generate topic validation analysis (if available)
        topic_analysis = self._analyze_topic_validation(all_identifiers)

        # Generate paper classifications
        paper_classifications = self._classify_papers(all_identifiers)

        # Calculate F1 metrics for statistical assessment
        f1_metrics = self.calculate_f1_metrics(all_identifiers)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            stats, validation_analysis, topic_analysis
        )

        # Compile complete report
        report: Dict[str, Any] = {
            "metadata": {
                "report_name": report_name,
                "generated_at": datetime.now().isoformat(),
                "total_extraction_results": len(results),
                "total_identifiers": len(all_identifiers),
            },
            "summary_statistics": stats,
            "validation_analysis": validation_analysis,
            "stratified_analysis": stratified_analysis,
            "failure_analysis": failure_analysis,
            "topic_analysis": topic_analysis,
            "f1_metrics": f1_metrics,
            "paper_classifications": paper_classifications,
            "recommendations": recommendations,
        }

        if include_detailed_papers:
            report["detailed_papers"] = self._generate_paper_details(all_identifiers)

        # Save reports in multiple formats
        self._save_report(report, report_name)

        logger.info(f"Validation report generated successfully: {report_name}")
        return report

    def _generate_comprehensive_stats(
        self,
        results: List[IdentifierExtractionResult],
        identifiers: List[AcademicIdentifier],
    ) -> Dict[str, Any]:
        """Generate comprehensive statistics across all results."""
        stats = {
            "extraction_performance": {
                "total_urls_processed": sum(
                    r.extraction_stats.get("total_urls", 0) for r in results
                ),
                "successful_extractions": sum(
                    r.extraction_stats.get("successful_extractions", 0) for r in results
                ),
                "failed_extractions": sum(
                    r.extraction_stats.get("failed_extractions", 0) for r in results
                ),
                "avg_success_rate": 0.0,
                "avg_processing_time": (
                    sum(r.processing_time for r in results) / len(results)
                    if results
                    else 0.0
                ),
            },
            "identifier_types": {
                "doi_count": len(
                    [i for i in identifiers if i.type == IdentifierType.DOI]
                ),
                "pmid_count": len(
                    [i for i in identifiers if i.type == IdentifierType.PMID]
                ),
                "pmc_count": len(
                    [i for i in identifiers if i.type == IdentifierType.PMC]
                ),
            },
            "confidence_distribution": self._analyze_confidence_distribution(
                identifiers
            ),
            "extraction_methods": self._analyze_extraction_methods(identifiers),
        }

        # Calculate average success rate
        total_urls = stats["extraction_performance"]["total_urls_processed"]
        if total_urls > 0:
            stats["extraction_performance"]["avg_success_rate"] = (
                stats["extraction_performance"]["successful_extractions"] / total_urls
            )

        return stats

    def _analyze_stratified_performance(
        self,
        identifiers: List[AcademicIdentifier],
        failed_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Analyze performance stratified by extraction method."""
        from .base import ExtractionMethod

        if failed_urls is None:
            failed_urls = []

        # Group identifiers by extraction method
        by_method: Dict[Any, List[AcademicIdentifier]] = {
            ExtractionMethod.URL_PATTERN: [],
            ExtractionMethod.WEB_SCRAPING: [],
            ExtractionMethod.PDF_EXTRACTION: [],
        }

        for identifier in identifiers:
            if identifier.extraction_method in by_method:
                by_method[identifier.extraction_method].append(identifier)

        # Calculate statistics for each method
        stratified_stats = {}
        total_successes = len(identifiers)
        total_attempts = total_successes + len(failed_urls)

        for method, method_identifiers in by_method.items():
            method_name = method.value
            count = len(method_identifiers)

            # Calculate confidence stats
            if method_identifiers:
                confidences = [i.confidence for i in method_identifiers]
                avg_confidence = sum(confidences) / len(confidences)
                high_conf_count = len(
                    [i for i in method_identifiers if i.confidence >= 0.8]
                )

                # Topic validation stats if available
                topic_validated = [
                    i for i in method_identifiers if i.topic_validation is not None
                ]
                topic_stats = {}
                if topic_validated:
                    relevant_count = len(
                        [
                            i
                            for i in topic_validated
                            if i.topic_validation
                            and i.topic_validation.get("is_relevant", False)
                        ]
                    )
                    topic_stats = {
                        "total_validated": len(topic_validated),
                        "relevant_papers": relevant_count,
                        "relevance_rate": (
                            relevant_count / len(topic_validated)
                            if topic_validated
                            else 0
                        ),
                        "avg_topic_confidence": (
                            sum(
                                i.topic_validation.get("confidence", 0)
                                for i in topic_validated
                                if i.topic_validation
                            )
                            / len(topic_validated)
                            if topic_validated
                            else 0
                        ),
                    }
            else:
                avg_confidence = 0
                high_conf_count = 0
                topic_stats = {}

            stratified_stats[method_name] = {
                "total_identifiers": count,
                "success_rate": count / total_attempts if total_attempts > 0 else 0,
                "avg_confidence": avg_confidence,
                "high_confidence_count": high_conf_count,
                "high_confidence_rate": high_conf_count / count if count > 0 else 0,
                "topic_validation": topic_stats,
                "identifier_types": {
                    "doi": len(
                        [i for i in method_identifiers if i.type.value == "doi"]
                    ),
                    "pmid": len(
                        [i for i in method_identifiers if i.type.value == "pmid"]
                    ),
                    "pmc": len(
                        [i for i in method_identifiers if i.type.value == "pmc"]
                    ),
                },
            }

        # Overall summary
        summary = {
            "total_identifiers": total_successes,
            "total_failed_urls": len(failed_urls),
            "overall_success_rate": (
                total_successes / total_attempts if total_attempts > 0 else 0
            ),
            "extraction_method_breakdown": {
                "url_pattern_percentage": (
                    len(by_method[ExtractionMethod.URL_PATTERN]) / total_successes * 100
                    if total_successes > 0
                    else 0
                ),
                "web_scraping_percentage": (
                    len(by_method[ExtractionMethod.WEB_SCRAPING])
                    / total_successes
                    * 100
                    if total_successes > 0
                    else 0
                ),
                "pdf_extraction_percentage": (
                    len(by_method[ExtractionMethod.PDF_EXTRACTION])
                    / total_successes
                    * 100
                    if total_successes > 0
                    else 0
                ),
            },
        }

        return {
            "stratified_performance": stratified_stats,
            "summary": summary,
            "method_comparison": self._compare_extraction_methods(by_method),
        }

    def _compare_extraction_methods(
        self, by_method: Dict[Any, List[AcademicIdentifier]]
    ) -> Dict[str, Any]:
        """Compare performance across extraction methods."""
        from .base import ExtractionMethod

        comparison: Dict[str, Any] = {
            "best_method_by_count": None,
            "best_method_by_confidence": None,
            "best_method_by_relevance": None,
            "recommendations": [],
        }

        # Find best method by count
        counts = {
            method.value: len(identifiers) for method, identifiers in by_method.items()
        }
        if any(counts.values()):
            best_count_method = max(counts.items(), key=lambda x: x[1])
            comparison["best_method_by_count"] = {
                "method": best_count_method[0],
                "count": best_count_method[1],
            }

        # Find best method by confidence
        avg_confidences = {}
        for method, identifiers in by_method.items():
            if identifiers:
                avg_conf = sum(i.confidence for i in identifiers) / len(identifiers)
                avg_confidences[method.value] = avg_conf

        if avg_confidences:
            best_conf_method = max(avg_confidences.items(), key=lambda x: x[1])
            comparison["best_method_by_confidence"] = {
                "method": best_conf_method[0],
                "confidence": best_conf_method[1],
            }

        # Generate recommendations based on performance
        total_identifiers = sum(len(identifiers) for identifiers in by_method.values())
        if total_identifiers > 0:
            url_pattern_rate = (
                len(by_method.get(ExtractionMethod.URL_PATTERN, [])) / total_identifiers
            )
            web_scraping_rate = (
                len(by_method.get(ExtractionMethod.WEB_SCRAPING, []))
                / total_identifiers
            )
            pdf_rate = (
                len(by_method.get(ExtractionMethod.PDF_EXTRACTION, []))
                / total_identifiers
            )

            if url_pattern_rate > 0.8:
                comparison["recommendations"].append(
                    "Excellent URL pattern extraction - most papers have direct identifiers"
                )
            elif web_scraping_rate > 0.4:
                comparison["recommendations"].append(
                    "Significant web scraping usage - consider improving URL pattern detection"
                )
            elif pdf_rate > 0.2:
                comparison["recommendations"].append(
                    "High PDF extraction rate - many papers only available as PDFs"
                )

            if url_pattern_rate < 0.3:
                comparison["recommendations"].append(
                    "Low direct URL extraction - review URL pattern matching"
                )

        return comparison

    def _analyze_validation_performance(
        self, identifiers: List[AcademicIdentifier]
    ) -> Dict[str, Any]:
        """Analyze validation method performance."""
        analysis: Dict[str, Any] = {
            "validation_methods_used": [],
            "confidence_by_method": {},
            "validation_agreement": {},
        }

        # Count validation methods used (inferred from confidence patterns)
        high_conf = len([i for i in identifiers if i.confidence >= 0.9])
        medium_conf = len([i for i in identifiers if 0.7 <= i.confidence < 0.9])
        low_conf = len([i for i in identifiers if i.confidence < 0.7])

        analysis["confidence_ranges"] = {
            "high_confidence_90_plus": high_conf,
            "medium_confidence_70_89": medium_conf,
            "low_confidence_below_70": low_conf,
            "total": len(identifiers),
        }

        if identifiers:
            analysis["avg_confidence"] = sum(i.confidence for i in identifiers) / len(
                identifiers
            )
            analysis["min_confidence"] = min(i.confidence for i in identifiers)
            analysis["max_confidence"] = max(i.confidence for i in identifiers)

        return analysis

    def _analyze_topic_validation(
        self, identifiers: List[AcademicIdentifier]
    ) -> Dict[str, Any]:
        """Analyze topic validation results if available."""
        topic_validated = [i for i in identifiers if i.topic_validation is not None]

        if not topic_validated:
            return {
                "topic_validation_available": False,
                "message": "No topic validation data found",
            }

        analysis: Dict[str, Any] = {
            "topic_validation_available": True,
            "total_validated": len(topic_validated),
            "relevant_papers": 0,
            "irrelevant_papers": 0,
            "uncertain_papers": 0,
            "validation_errors": 0,
            "confidence_distribution": {
                "high_confidence_80_plus": 0,
                "medium_confidence_50_79": 0,
                "low_confidence_below_50": 0,
            },
            "avg_topic_confidence": 0.0,
            "common_keywords": {},
        }

        confidence_scores = []
        all_keywords = []

        for identifier in topic_validated:
            tv = identifier.topic_validation
            if tv is None:
                continue

            # Count relevance classifications
            if tv.get("is_relevant") is True:
                analysis["relevant_papers"] += 1
            elif tv.get("is_relevant") is False:
                analysis["irrelevant_papers"] += 1
            elif tv.get("is_relevant") is None:
                if "failed" in tv.get("reasoning", "").lower():
                    analysis["validation_errors"] += 1
                else:
                    analysis["uncertain_papers"] += 1

            # Analyze confidence scores
            confidence = tv.get("confidence", 0)
            if confidence >= 80:
                analysis["confidence_distribution"]["high_confidence_80_plus"] += 1
            elif confidence >= 50:
                analysis["confidence_distribution"]["medium_confidence_50_79"] += 1
            else:
                analysis["confidence_distribution"]["low_confidence_below_50"] += 1

            if confidence > 0:
                confidence_scores.append(confidence)

            # Collect keywords
            keywords = tv.get("keywords_found", [])
            all_keywords.extend(keywords)

        # Calculate average confidence
        if confidence_scores:
            analysis["avg_topic_confidence"] = sum(confidence_scores) / len(
                confidence_scores
            )

        # Count keyword frequency
        keyword_counts: Dict[str, int] = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Get top 10 most common keywords
        analysis["common_keywords"] = dict(
            sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        return analysis

    def _classify_papers(
        self, identifiers: List[AcademicIdentifier]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Classify papers for manual review recommendations."""
        classifications: Dict[str, List[Dict[str, Any]]] = {
            "high_confidence_relevant": [],
            "medium_confidence_relevant": [],
            "low_confidence_relevant": [],
            "likely_irrelevant": [],
            "needs_manual_review": [],
            "validation_errors": [],
        }

        for identifier in identifiers:
            paper_info: Dict[str, Any] = {
                "identifier_type": identifier.type.value,
                "identifier_value": identifier.value,
                "extraction_confidence": identifier.confidence,
                "source_url": identifier.source_url,
            }

            if identifier.topic_validation:
                tv = identifier.topic_validation
                paper_info.update(
                    {
                        "topic_relevant": tv.get("is_relevant"),
                        "topic_confidence": tv.get("confidence", 0),
                        "topic_reasoning": tv.get("reasoning", ""),
                        "keywords_found": tv.get("keywords_found", []),
                    }
                )

                # Classify based on topic validation
                if tv.get("is_relevant") is True:
                    if tv.get("confidence", 0) >= 80:
                        classifications["high_confidence_relevant"].append(paper_info)
                    elif tv.get("confidence", 0) >= 50:
                        classifications["medium_confidence_relevant"].append(paper_info)
                    else:
                        classifications["low_confidence_relevant"].append(paper_info)
                elif tv.get("is_relevant") is False:
                    classifications["likely_irrelevant"].append(paper_info)
                elif "failed" in tv.get("reasoning", "").lower():
                    classifications["validation_errors"].append(paper_info)
                else:
                    classifications["needs_manual_review"].append(paper_info)
            else:
                # No topic validation - classify by extraction confidence
                if identifier.confidence >= 0.8:
                    classifications["needs_manual_review"].append(paper_info)
                else:
                    classifications["needs_manual_review"].append(paper_info)

        return classifications

    def _generate_recommendations(
        self,
        stats: Dict[str, Any],
        validation_analysis: Dict[str, Any],
        topic_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Extraction performance recommendations
        success_rate = stats["extraction_performance"]["avg_success_rate"]
        if success_rate < 0.7:
            recommendations.append(
                f"🔧 Low extraction success rate ({success_rate:.1%}). Consider improving URL pattern matching or expanding web scraping capabilities."
            )

        # Confidence distribution recommendations
        low_conf_count = validation_analysis["confidence_ranges"][
            "low_confidence_below_70"
        ]
        total_count = validation_analysis["confidence_ranges"]["total"]
        if total_count > 0 and low_conf_count / total_count > 0.3:
            recommendations.append(
                f"⚠️ High proportion of low-confidence identifiers ({low_conf_count}/{total_count}). Consider additional validation methods."
            )

        # Topic validation recommendations
        if topic_analysis.get("topic_validation_available"):
            irrelevant_count = topic_analysis.get("irrelevant_papers", 0)
            total_validated = topic_analysis.get("total_validated", 0)
            if total_validated > 0 and irrelevant_count / total_validated > 0.2:
                recommendations.append(
                    f"📋 Significant number of irrelevant papers found ({irrelevant_count}/{total_validated}). Consider refining source URL selection."
                )

            avg_topic_conf = topic_analysis.get("avg_topic_confidence", 0)
            if avg_topic_conf < 70:
                recommendations.append(
                    f"🤖 Low average topic validation confidence ({avg_topic_conf:.1f}). Consider adjusting LLM prompts or model parameters."
                )

            error_count = topic_analysis.get("validation_errors", 0)
            if error_count > 0:
                recommendations.append(
                    f"🔍 {error_count} topic validation errors occurred. Check NCBI API connectivity and rate limits."
                )
        else:
            recommendations.append(
                "💡 Consider enabling topic validation to assess paper relevance to astrocyte biology."
            )

        # Manual review recommendations
        if not recommendations:
            recommendations.append(
                "✅ Validation performance looks good! Consider proceeding with manual spot-checking of medium confidence papers."
            )

        return recommendations

    def _generate_paper_details(
        self, identifiers: List[AcademicIdentifier]
    ) -> List[Dict[str, Any]]:
        """Generate detailed paper information for export."""
        details = []
        for identifier in identifiers:
            paper: Dict[str, Any] = {
                "identifier_type": identifier.type.value,
                "identifier_value": identifier.value,
                "extraction_confidence": identifier.confidence,
                "source_url": identifier.source_url,
                "extraction_method": identifier.extraction_method.value,
                "timestamp": identifier.timestamp,
            }

            if identifier.topic_validation:
                paper["topic_validation"] = identifier.topic_validation

            details.append(paper)

        return details

    def _analyze_confidence_distribution(
        self, identifiers: List[AcademicIdentifier]
    ) -> Dict[str, int]:
        """Analyze distribution of confidence scores."""
        distribution = {
            "0.9-1.0": 0,
            "0.8-0.89": 0,
            "0.7-0.79": 0,
            "0.6-0.69": 0,
            "0.5-0.59": 0,
            "below_0.5": 0,
        }

        for identifier in identifiers:
            conf = identifier.confidence
            if conf >= 0.9:
                distribution["0.9-1.0"] += 1
            elif conf >= 0.8:
                distribution["0.8-0.89"] += 1
            elif conf >= 0.7:
                distribution["0.7-0.79"] += 1
            elif conf >= 0.6:
                distribution["0.6-0.69"] += 1
            elif conf >= 0.5:
                distribution["0.5-0.59"] += 1
            else:
                distribution["below_0.5"] += 1

        return distribution

    def _analyze_extraction_methods(
        self, identifiers: List[AcademicIdentifier]
    ) -> Dict[str, int]:
        """Analyze distribution of extraction methods."""
        methods: Dict[str, int] = {}
        for identifier in identifiers:
            method = identifier.extraction_method.value
            methods[method] = methods.get(method, 0) + 1
        return methods

    def _save_report(self, report: Dict[str, Any], report_name: str) -> None:
        """Save report in multiple formats."""
        # Save as JSON
        json_path = self.output_dir / f"{report_name}.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Save summary as text
        text_path = self.output_dir / f"{report_name}_summary.txt"
        with open(text_path, "w") as f:
            f.write(self._format_text_summary(report))

        # Save CSV for detailed analysis
        if "detailed_papers" in report:
            self._save_csv_export(
                report["detailed_papers"], f"{report_name}_papers.csv"
            )

        logger.info(f"Reports saved to {self.output_dir}")

    def _format_text_summary(self, report: Dict[str, Any]) -> str:
        """Format a human-readable text summary."""
        lines = []
        lines.append("=" * 60)
        lines.append("VALIDATION ASSESSMENT REPORT")
        lines.append(f"Generated: {report['metadata']['generated_at']}")
        lines.append("=" * 60)
        lines.append("")

        # Summary statistics
        stats = report["summary_statistics"]
        lines.append("📊 EXTRACTION PERFORMANCE")
        lines.append(
            f"  Total URLs processed: {stats['extraction_performance']['total_urls_processed']}"
        )
        lines.append(
            f"  Successful extractions: {stats['extraction_performance']['successful_extractions']}"
        )
        lines.append(
            f"  Success rate: {stats['extraction_performance']['avg_success_rate']:.1%}"
        )
        lines.append(
            f"  Average processing time: {stats['extraction_performance']['avg_processing_time']:.2f}s"
        )
        lines.append("")

        lines.append("🔬 IDENTIFIER TYPES")
        types = stats["identifier_types"]
        lines.append(f"  DOI: {types['doi_count']}")
        lines.append(f"  PMID: {types['pmid_count']}")
        lines.append(f"  PMC: {types['pmc_count']}")
        lines.append("")

        # Topic validation
        topic = report["topic_analysis"]
        if topic.get("topic_validation_available"):
            lines.append("🎯 TOPIC VALIDATION RESULTS")
            lines.append(f"  Total validated: {topic['total_validated']}")
            lines.append(f"  Relevant papers: {topic['relevant_papers']}")
            lines.append(f"  Irrelevant papers: {topic['irrelevant_papers']}")
            lines.append(
                f"  Average topic confidence: {topic['avg_topic_confidence']:.1f}"
            )
            lines.append("")

        # F1 Metrics
        f1_metrics = report.get("f1_metrics", {})
        if f1_metrics:
            lines.append("📈 F1 SCORE ASSESSMENT")

            # Extraction F1
            ext_f1 = f1_metrics.get("extraction_f1", {})
            lines.append(f"  Extraction F1 Score: {ext_f1.get('f1_score', 0):.3f}")
            lines.append(f"  Extraction Precision: {ext_f1.get('precision', 0):.3f}")
            lines.append(f"  Extraction Recall: {ext_f1.get('recall', 0):.3f}")

            # Topic F1 if available
            topic_f1 = f1_metrics.get("topic_validation_f1", {})
            if topic_f1.get("validation_available"):
                lines.append(f"  Topic F1 Score: {topic_f1.get('f1_score', 0):.3f}")
                lines.append(f"  Topic Precision: {topic_f1.get('precision', 0):.3f}")
                lines.append(f"  Topic Recall: {topic_f1.get('recall', 0):.3f}")

            # Overall assessment
            assessment = f1_metrics.get("combined_assessment", {})
            if "overall_grade" in assessment:
                lines.append(f"  Overall Grade: {assessment['overall_grade']}")

            lines.append("")

        # Recommendations
        lines.append("💡 RECOMMENDATIONS")
        for rec in report["recommendations"]:
            lines.append(f"  {rec}")
        lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def calculate_f1_metrics(
        self,
        identifiers: List[AcademicIdentifier],
        true_positives_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """Calculate F1 scores for validation assessment.

        Args:
            identifiers: List of extracted identifiers with validation data
            true_positives_threshold: Confidence threshold for considering extraction successful

        Returns:
            Dictionary containing F1 metrics for extraction and topic validation
        """
        logger.info("Calculating F1 metrics for validation assessment")

        # Calculate extraction F1 score
        extraction_metrics = self._calculate_extraction_f1(
            identifiers, true_positives_threshold
        )

        # Calculate topic validation F1 score if available
        topic_metrics = self._calculate_topic_validation_f1(identifiers)

        # Combined metrics
        f1_metrics = {
            "extraction_f1": extraction_metrics,
            "topic_validation_f1": topic_metrics,
            "combined_assessment": self._assess_combined_performance(
                extraction_metrics, topic_metrics
            ),
            "sample_size": len(identifiers),
            "confidence_threshold": true_positives_threshold,
        }

        return f1_metrics

    def _calculate_extraction_f1(
        self, identifiers: List[AcademicIdentifier], threshold: float
    ) -> Dict[str, float]:
        """Calculate F1 score for identifier extraction accuracy.

        This evaluates whether we correctly extracted identifiers from academic URLs.
        High confidence (>threshold) = True Positive
        Medium confidence (0.5-threshold) = Uncertain
        Low confidence (<0.5) = False Positive (likely wrong extraction)
        """
        if not identifiers:
            return {"precision": 0.0, "recall": 1.0, "f1_score": 0.0, "support": 0}

        # Classify extractions based on confidence
        high_confidence = [i for i in identifiers if i.confidence >= threshold]
        medium_confidence = [i for i in identifiers if 0.5 <= i.confidence < threshold]
        low_confidence = [i for i in identifiers if i.confidence < 0.5]

        # Extraction metrics:
        # True Positives: High confidence extractions (likely correct)
        # False Positives: Low confidence extractions (likely incorrect)
        # False Negatives: We assume some URLs didn't yield identifiers (conservative estimate)

        true_positives = len(high_confidence)
        false_positives = len(low_confidence)

        # Estimate false negatives: assume 90% of academic URLs should yield identifiers
        total_expected_identifiers = int(
            len(identifiers) * 1.1
        )  # Conservative estimate
        false_negatives = max(0, total_expected_identifiers - len(identifiers))

        # Calculate metrics
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "medium_confidence": len(medium_confidence),
            "support": len(identifiers),
        }

    def _calculate_topic_validation_f1(
        self, identifiers: List[AcademicIdentifier]
    ) -> Dict[str, Any]:
        """Calculate F1 score for topic validation accuracy.

        This evaluates how well we classify papers as relevant/irrelevant to the research domain.
        """
        # Filter identifiers that have topic validation
        topic_validated = [i for i in identifiers if i.topic_validation is not None]

        if not topic_validated:
            return {
                "precision": None,
                "recall": None,
                "f1_score": None,
                "support": 0,
                "validation_available": False,
            }

        # Classify based on topic validation results
        relevant_papers = [
            i
            for i in topic_validated
            if i.topic_validation and i.topic_validation.get("is_relevant", False)
        ]
        irrelevant_papers = [
            i
            for i in topic_validated
            if i.topic_validation and not i.topic_validation.get("is_relevant", True)
        ]

        # High confidence topic classifications
        high_conf_relevant = [
            i
            for i in relevant_papers
            if i.topic_validation and i.topic_validation.get("confidence", 0) >= 80
        ]
        high_conf_irrelevant = [
            i
            for i in irrelevant_papers
            if i.topic_validation and i.topic_validation.get("confidence", 0) >= 80
        ]

        # For F1 calculation:
        # True Positives: High confidence relevant papers
        # False Positives: Low confidence relevant papers (might be wrong)
        # False Negatives: High confidence irrelevant papers (should have been relevant for this corpus)

        true_positives = len(high_conf_relevant)

        # Low confidence relevant classifications as potential false positives
        low_conf_relevant = [
            i
            for i in relevant_papers
            if i.topic_validation and i.topic_validation.get("confidence", 0) < 80
        ]
        false_positives = len(low_conf_relevant)

        # High confidence irrelevant papers as false negatives (since our corpus should be relevant)
        false_negatives = len(high_conf_irrelevant)

        # Calculate metrics
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        # Additional topic validation metrics
        avg_confidence = sum(
            i.topic_validation.get("confidence", 0)
            for i in topic_validated
            if i.topic_validation
        ) / len(topic_validated)
        relevance_rate = len(relevant_papers) / len(topic_validated)

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "support": len(topic_validated),
            "validation_available": True,
            "relevance_rate": relevance_rate,
            "avg_confidence": avg_confidence,
            "total_relevant": len(relevant_papers),
            "total_irrelevant": len(irrelevant_papers),
        }

    def _assess_combined_performance(
        self, extraction_metrics: Dict[str, float], topic_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall validation performance combining extraction and topic metrics."""

        extraction_f1 = extraction_metrics.get("f1_score", 0.0)
        topic_f1 = (
            topic_metrics.get("f1_score")
            if topic_metrics.get("validation_available")
            else None
        )

        assessment: Dict[str, Any] = {
            "extraction_grade": self._grade_score(extraction_f1),
            "topic_grade": (
                self._grade_score(topic_f1) if topic_f1 is not None else "N/A"
            ),
        }

        if topic_f1 is not None:
            # Combined score: weighted average (extraction 60%, topic 40%)
            combined_f1 = 0.6 * extraction_f1 + 0.4 * topic_f1
            assessment["combined_f1"] = combined_f1
            assessment["overall_grade"] = self._grade_score(combined_f1)

            # Specific recommendations
            recommendations = []
            if extraction_f1 < 0.7:
                recommendations.append(
                    "Improve extraction accuracy by refining URL patterns and web scraping"
                )
            if topic_f1 < 0.7:
                recommendations.append(
                    "Improve topic validation by refining LLM prompts or domain definitions"
                )
            if combined_f1 >= 0.8:
                recommendations.append(
                    "Validation performance is excellent - ready for production use"
                )
            elif combined_f1 >= 0.6:
                recommendations.append(
                    "Good validation performance - consider minor optimizations"
                )
            else:
                recommendations.append(
                    "Validation needs improvement before production use"
                )

            assessment["recommendations"] = recommendations
        else:
            assessment["combined_f1"] = extraction_f1
            assessment["overall_grade"] = assessment["extraction_grade"]
            assessment["recommendations"] = [
                "Enable topic validation for comprehensive assessment"
            ]

        return assessment

    def _grade_score(self, score: Optional[float]) -> str:
        """Convert F1 score to letter grade."""
        if score is None:
            return "N/A"
        if score >= 0.9:
            return "A+ (Excellent)"
        elif score >= 0.8:
            return "A (Very Good)"
        elif score >= 0.7:
            return "B (Good)"
        elif score >= 0.6:
            return "C (Fair)"
        elif score >= 0.5:
            return "D (Poor)"
        else:
            return "F (Failing)"

    def _save_csv_export(self, papers: List[Dict[str, Any]], filename: str) -> None:
        """Save detailed paper data as CSV."""
        import csv

        csv_path = self.output_dir / filename

        if not papers:
            return

        # Get all possible fieldnames
        fieldnames_set: set[str] = set()
        for paper in papers:
            fieldnames_set.update(paper.keys())
            if "topic_validation" in paper and paper["topic_validation"]:
                for key in paper["topic_validation"].keys():
                    fieldnames_set.add(f"topic_{key}")

        fieldnames = sorted(fieldnames_set)

        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for paper in papers:
                row = paper.copy()

                # Flatten topic validation data
                if "topic_validation" in row and row["topic_validation"]:
                    tv = row.pop("topic_validation")
                    for key, value in tv.items():
                        row[f"topic_{key}"] = value

                # Convert lists to strings
                for key, value in row.items():
                    if isinstance(value, list):
                        row[key] = "; ".join(str(v) for v in value)

                writer.writerow(row)

        logger.info(f"CSV export saved: {csv_path}")

    def _generate_failure_analysis(
        self, results: List[IdentifierExtractionResult]
    ) -> Dict[str, Any]:
        """Generate comprehensive failure analysis with simple list format."""
        all_failed_urls = []
        failure_stats: Dict[str, Any] = {
            "total_failed_urls": 0,
            "failure_by_domain": {},
            "failure_patterns": {
                "pdf_links": 0,
                "redirect_issues": 0,
                "access_denied": 0,
                "timeout_errors": 0,
                "format_issues": 0,
                "unknown_errors": 0,
            },
            "detailed_failures": [],
        }

        # Collect all failed URLs from results
        for result in results:
            for failed_url in result.failed_urls:
                all_failed_urls.append(failed_url)

                # Extract domain for categorization
                try:
                    from urllib.parse import urlparse

                    domain = urlparse(failed_url).netloc
                    failure_stats["failure_by_domain"][domain] = (
                        failure_stats["failure_by_domain"].get(domain, 0) + 1
                    )
                except Exception:
                    failure_stats["failure_by_domain"]["unknown"] = (
                        failure_stats["failure_by_domain"].get("unknown", 0) + 1
                    )

                # Categorize failure type based on URL pattern
                failure_entry = {
                    "url": failed_url,
                    "category": self._categorize_failure(failed_url),
                    "domain": domain if "domain" in locals() else "unknown",
                }

                failure_stats["detailed_failures"].append(failure_entry)

                # Update pattern counters
                category = failure_entry["category"]
                if category in failure_stats["failure_patterns"]:
                    failure_stats["failure_patterns"][category] += 1

        failure_stats["total_failed_urls"] = len(all_failed_urls)

        # Generate simple failure list for easy review
        failure_stats["simple_failure_list"] = [
            f"{entry['url']} (Category: {entry['category']}, Domain: {entry['domain']})"
            for entry in failure_stats["detailed_failures"]
        ]

        # Add recommendations
        failure_stats["recommendations"] = self._generate_failure_recommendations(
            failure_stats
        )

        return failure_stats

    def _categorize_failure(self, url: str) -> str:
        """Categorize failure type based on URL characteristics."""
        url_lower = url.lower()

        if url_lower.endswith(".pdf"):
            return "pdf_links"
        elif "doi.org" in url_lower or "dx.doi.org" in url_lower:
            return "redirect_issues"
        elif "access" in url_lower or "login" in url_lower:
            return "access_denied"
        elif any(pattern in url_lower for pattern in ["pubmed", "ncbi", "pmc"]):
            return "format_issues"  # Likely format/parsing issues
        else:
            return "unknown_errors"

    def _generate_failure_recommendations(
        self, failure_stats: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on failure patterns."""
        recommendations = []
        total_failures = failure_stats["total_failed_urls"]
        patterns = failure_stats["failure_patterns"]

        if total_failures == 0:
            recommendations.append("Excellent! No URL extraction failures detected.")
            return recommendations

        # Specific recommendations based on failure patterns
        if patterns["pdf_links"] > total_failures * 0.3:
            recommendations.append(
                f"High PDF failure rate ({patterns['pdf_links']}/{total_failures}) - "
                "Consider improving PDF text extraction or LLM processing"
            )

        if patterns["redirect_issues"] > total_failures * 0.2:
            recommendations.append(
                f"Redirect issues detected ({patterns['redirect_issues']}/{total_failures}) - "
                "Review DOI resolution and redirect handling"
            )

        if patterns["access_denied"] > 0:
            recommendations.append(
                f"Access denied issues ({patterns['access_denied']}/{total_failures}) - "
                "Some papers may be behind paywalls or require authentication"
            )

        if patterns["format_issues"] > total_failures * 0.4:
            recommendations.append(
                f"Format/parsing issues ({patterns['format_issues']}/{total_failures}) - "
                "Review URL pattern matching and metadata extraction"
            )

        # Domain-specific recommendations
        domain_stats = failure_stats["failure_by_domain"]
        if domain_stats:
            top_failing_domain = max(domain_stats.items(), key=lambda x: x[1])
            if top_failing_domain[1] > 3:  # More than 3 failures from same domain
                recommendations.append(
                    f"Domain '{top_failing_domain[0]}' has {top_failing_domain[1]} failures - "
                    "investigate site-specific extraction issues"
                )

        # Overall failure rate recommendation
        if total_failures > 50:
            recommendations.append(
                f"High overall failure count ({total_failures}) - "
                "consider reviewing URL quality and extraction robustness"
            )

        return recommendations
