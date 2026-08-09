#!/usr/bin/env python3
"""
Passage Metadata Analysis & Query-Time Enrichment

This script provides:
1. Analysis of existing passages to understand coverage and quality
2. Query-time enrichment functions for use during RAG search
3. Validation of passage metadata

NOTE: The Letta API does not support passage tag updates (no PATCH endpoint).
Therefore, this script operates in ANALYSIS mode - computing metadata without
modifying passages. The computed metadata can be applied at QUERY TIME
by the letta_workflow.py when formatting search results.

Usage:
    # Analyze passages and generate report
    python -m CONTENT_CREATOR_FRAMEWORK.scripts.enrich_existing_passages --archive db2_entity_qms --analyze

    # Validate existing tags
    python -m CONTENT_CREATOR_FRAMEWORK.scripts.enrich_existing_passages --archive all --validate
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration files
CONFIG_DIR = PROJECT_ROOT / "CONTENT_CREATOR_FRAMEWORK" / "config"


def load_config(filename: str) -> Dict[str, Any]:
    """Load JSON configuration file."""
    config_path = CONFIG_DIR / filename
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class PassageEnricher:
    """
    Enriches Letta archive passages with metadata tags.

    Performs non-destructive tag updates:
    - Preserves existing tags
    - Adds category, quality, year, reg_align, use_for tags
    - No re-embedding required
    """

    def __init__(self, base_url: str = "http://localhost:8283", api_key: str = "local"):
        """Initialize the enricher with Letta client connection."""
        try:
            from letta_client import Letta
            self.client = Letta(base_url=base_url, api_key=api_key, timeout=300)
            logger.info(f"Connected to Letta server at {base_url}")
        except ImportError:
            logger.error("letta_client not installed. Install with: pip install letta-client")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Letta server: {e}")
            raise

        # Load configuration
        self.kb_metadata = load_config("kb_metadata_config.json")
        self.classification_rules = load_config("category_classification_rules.json")

        # Cache for archives
        self._archives: Dict[str, Any] = {}

    def _get_archive(self, archive_name: str) -> Optional[Any]:
        """Get archive by name, with caching."""
        if archive_name in self._archives:
            return self._archives[archive_name]

        try:
            # Use correct API: archives (not sources)
            archives = list(self.client.archives.list())
            for archive in archives:
                if archive.name == archive_name:
                    self._archives[archive_name] = archive
                    return archive
            logger.warning(f"Archive not found: {archive_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to list archives: {e}")
            return None

    def _classify_category(self, tags: List[str], text: str) -> str:
        """
        Classify document category from existing tags and text content.

        Priority:
        1. Filename patterns in existing tags
        2. Content keywords in text
        """
        rules = self.classification_rules.get("classification_rules", {})
        filename_patterns = rules.get("filename_patterns", {})
        content_keywords = rules.get("content_keywords", {})

        # Extract filename from tags
        filename = ""
        for tag in tags:
            if tag.startswith("file:"):
                filename = tag[5:].lower()
                break

        # Check filename patterns
        if filename:
            for category, config in filename_patterns.items():
                patterns = config.get("patterns", [])
                if any(pattern in filename for pattern in patterns):
                    return category

        # Fallback: content-based classification
        text_lower = text.lower()[:3000]  # First 3000 chars
        category_scores = {}

        for category, config in content_keywords.items():
            keywords = config.get("keywords", [])
            weight = config.get("weight", 0.8)
            score = sum(weight for kw in keywords if kw in text_lower)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            return max(category_scores, key=category_scores.get)

        return "General"

    def _calculate_quality_score(self, text: str) -> float:
        """
        Calculate document quality score (0-10) based on structure and content.
        """
        score = 0.0
        scoring = self.classification_rules.get("quality_scoring", {})

        # Structure indicators
        structure = scoring.get("structure_indicators", {})

        # Check for headers (markdown)
        if re.search(r"^#{1,3}\s+\w+", text, re.MULTILINE):
            score += structure.get("has_headers", {}).get("points", 2.5)

        # Check for numbered lists
        if re.search(r"^\d+\.\s+\w+", text, re.MULTILINE):
            score += structure.get("has_numbering", {}).get("points", 2.0)

        # Check for tables
        if "|" in text and "---" in text:
            score += structure.get("has_tables", {}).get("points", 1.5)

        # Check for bullet lists
        if re.search(r"^[-*]\s+", text, re.MULTILINE):
            score += structure.get("has_bullet_lists", {}).get("points", 1.0)

        # Content indicators
        content = scoring.get("content_indicators", {})
        text_lower = text.lower()

        for indicator_name, config in content.items():
            keywords = config.get("keywords", [])
            points = config.get("points", 1.0)
            if any(kw in text_lower for kw in keywords):
                score += points

        # Length scoring
        length_scoring = scoring.get("length_scoring", {})
        word_count = len(text.split())
        min_words = length_scoring.get("optimal_min_words", 500)
        max_words = length_scoring.get("optimal_max_words", 5000)
        if min_words <= word_count <= max_words:
            score += length_scoring.get("points", 0.5)

        # Cap at max score
        max_score = scoring.get("max_score", 10.0)
        return round(min(score, max_score), 1)

    def _extract_year(self, text: str, tags: List[str]) -> str:
        """Extract document year from text or tags."""
        # Check for year tag first
        for tag in tags:
            if tag.startswith("year:"):
                return tag[5:]

        # Search for year in text (common patterns)
        # "Effective Date: 2023", "Version 1.0 (2023)", "Date: 2023-01-15"
        year_patterns = [
            r'\b(202[0-9])\b',  # 2020-2029
            r'\b(201[0-9])\b',  # 2010-2019
        ]

        for pattern in year_patterns:
            match = re.search(pattern, text[:2000])  # First 2000 chars
            if match:
                return match.group(1)

        return "unknown"

    def _calculate_regulatory_alignment(self, text: str, category: str) -> float:
        """
        Calculate regulatory alignment score (0-10).

        Based on presence of regulatory references and GMP concepts.
        """
        scoring = self.classification_rules.get("regulatory_alignment_scoring", {})
        base_score = scoring.get("base_score", 5.0)
        max_score = scoring.get("max_score", 10.0)

        score = base_score
        text_lower = text.lower()

        # Check regulatory references
        reg_refs = scoring.get("regulatory_references", {})
        for term, points in reg_refs.items():
            if term in text_lower:
                score += points

        # Check GMP concepts
        gmp_concepts = scoring.get("gmp_concepts", {})
        keywords = gmp_concepts.get("keywords", [])
        points_each = gmp_concepts.get("points_each", 0.3)

        for keyword in keywords:
            if keyword in text_lower:
                score += points_each

        return round(min(score, max_score), 1)

    def _get_usage_recommendations(self, category: str) -> List[str]:
        """Get usage recommendations based on category."""
        rules = self.classification_rules.get("usage_recommendations", {})
        return rules.get(category, ["general_reference"])

    def _build_enriched_tags(
        self,
        existing_tags: List[str],
        category: str,
        quality: float,
        year: str,
        reg_align: float,
        usage_recommendations: List[str]
    ) -> List[str]:
        """
        Build enriched tag list preserving existing tags.

        Removes old metadata tags (category:, quality:, year:, reg_align:, use_for:)
        and adds new ones.
        """
        # Remove old metadata tags
        metadata_prefixes = ("category:", "quality:", "year:", "reg_align:", "use_for:")
        filtered_tags = [t for t in existing_tags if not t.startswith(metadata_prefixes)]

        # Add new metadata tags
        new_tags = [
            f"category:{category}",
            f"quality:{quality}",
            f"year:{year}",
            f"reg_align:{reg_align}",
        ]

        # Add usage recommendations
        for usage in usage_recommendations[:3]:  # Limit to 3 usage tags
            new_tags.append(f"use_for:{usage}")

        return filtered_tags + new_tags

    def analyze_archive(
        self,
        archive_name: str,
        sample_queries: List[str] = None,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """
        Analyze passages in an archive and compute metadata statistics.

        NOTE: This does NOT update passages (Letta API doesn't support tag updates).
        Instead, it computes metadata that can be applied at query time.

        Args:
            archive_name: Name of the Letta archive (e.g., "db2_entity_qms")
            sample_queries: List of queries to use for sampling passages
            sample_size: Number of passages to analyze per query

        Returns:
            Analysis report with category distribution, quality stats, etc.
        """
        archive = self._get_archive(archive_name)
        if not archive:
            logger.error(f"Archive not found: {archive_name}")
            return {"error": f"Archive not found: {archive_name}"}

        logger.info(f"Analyzing archive: {archive_name} (ID: {archive.id})")

        # Default queries to cover different topics
        if sample_queries is None:
            sample_queries = [
                "procedure", "sampling", "equipment", "cleaning",
                "documentation", "training", "quality", "production",
                "testing", "validation", "GMP"
            ]

        stats = {
            "archive_name": archive_name,
            "archive_id": archive.id,
            "total_analyzed": 0,
            "categories": {},
            "quality_scores": [],
            "years": {},
            "regulatory_alignment": [],
            "existing_tags_analysis": {},
            "sample_passages": []
        }

        seen_ids = set()

        for query in sample_queries:
            try:
                # Use search API to get passages (only way to list them)
                results = self.client.passages.search(
                    archive_id=archive.id,
                    query=query,
                    limit=sample_size
                )

                for result in results:
                    passage = result.passage
                    if passage.id in seen_ids:
                        continue
                    seen_ids.add(passage.id)

                    stats["total_analyzed"] += 1

                    try:
                        existing_tags = passage.tags or []
                        text = passage.text or ""

                        if not text.strip():
                            continue

                        # Compute metadata
                        category = self._classify_category(existing_tags, text)
                        quality = self._calculate_quality_score(text)
                        year = self._extract_year(text, existing_tags)
                        reg_align = self._calculate_regulatory_alignment(text, category)

                        # Update statistics
                        stats["categories"][category] = stats["categories"].get(category, 0) + 1
                        stats["quality_scores"].append(quality)
                        stats["years"][year] = stats["years"].get(year, 0) + 1
                        stats["regulatory_alignment"].append(reg_align)

                        # Analyze existing tags
                        for tag in existing_tags:
                            prefix = tag.split(":")[0] if ":" in tag else "untagged"
                            stats["existing_tags_analysis"][prefix] = (
                                stats["existing_tags_analysis"].get(prefix, 0) + 1
                            )

                        # Store sample passage data for validation
                        if len(stats["sample_passages"]) < 10:
                            stats["sample_passages"].append({
                                "id": passage.id[:20],
                                "category": category,
                                "quality": quality,
                                "year": year,
                                "reg_align": reg_align,
                                "existing_tags": existing_tags[:5],
                                "text_preview": text[:100]
                            })

                    except Exception as e:
                        logger.warning(f"Failed to analyze passage {passage.id}: {e}")

            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")

        # Calculate summary statistics
        if stats["quality_scores"]:
            stats["avg_quality"] = round(sum(stats["quality_scores"]) / len(stats["quality_scores"]), 2)
            stats["min_quality"] = min(stats["quality_scores"])
            stats["max_quality"] = max(stats["quality_scores"])

        if stats["regulatory_alignment"]:
            stats["avg_reg_align"] = round(
                sum(stats["regulatory_alignment"]) / len(stats["regulatory_alignment"]), 2
            )

        logger.info(f"Analysis complete for {archive_name}: {stats['total_analyzed']} passages")
        return stats

    def enrich_passage_at_query_time(
        self,
        passage_id: str,
        text: str,
        existing_tags: List[str]
    ) -> Dict[str, Any]:
        """
        Compute metadata for a single passage at query time.

        This is the function to call from letta_workflow.py when
        processing search results to add computed metadata.

        Args:
            passage_id: The passage ID
            text: The passage text
            existing_tags: Existing tags on the passage

        Returns:
            Dict with computed metadata: category, quality, year, reg_align, usage
        """
        category = self._classify_category(existing_tags, text)
        quality = self._calculate_quality_score(text)
        year = self._extract_year(text, existing_tags)
        reg_align = self._calculate_regulatory_alignment(text, category)
        usage_recs = self._get_usage_recommendations(category)

        return {
            "passage_id": passage_id,
            "category": category,
            "quality": quality,
            "year": year,
            "reg_align": reg_align,
            "usage_recommendations": usage_recs,
            "source_authority": "operational_example" if "entity" in str(existing_tags) else "official"
        }

    def analyze_all_archives(self) -> Dict[str, Dict[str, Any]]:
        """Analyze all configured archives."""
        results = {}

        for archive_name in ["db1_regulatory", "db2_entity_qms"]:
            logger.info(f"\n{'='*60}")
            logger.info(f"Analyzing archive: {archive_name}")
            logger.info(f"{'='*60}")
            results[archive_name] = self.analyze_archive(archive_name)

        return results

    def validate_passages(self, archive_name: str, sample_size: int = 10) -> None:
        """
        Validate passage structure and existing tags.

        Shows what metadata would be computed at query time for sample passages.
        """
        archive = self._get_archive(archive_name)
        if not archive:
            logger.error(f"Archive not found: {archive_name}")
            return

        logger.info(f"\nValidating passages in {archive_name}...")

        try:
            # Use search to get sample passages
            results = self.client.passages.search(
                archive_id=archive.id,
                query="procedure document",
                limit=sample_size
            )

            logger.info(f"Found {len(results)} passages to validate")
            logger.info("-" * 80)

            for result in results:
                passage = result.passage
                tags = passage.tags or []
                text = passage.text or ""

                # Compute metadata at query time
                metadata = self.enrich_passage_at_query_time(
                    passage_id=passage.id,
                    text=text,
                    existing_tags=tags
                )

                # Check existing tag coverage
                has_file = any(t.startswith("file:") for t in tags)
                has_entity = any(t.startswith("entity:") for t in tags)
                has_chunk = any(t.startswith("chunk:") for t in tags)

                tag_coverage = []
                if has_file:
                    tag_coverage.append("file")
                if has_entity:
                    tag_coverage.append("entity")
                if has_chunk:
                    tag_coverage.append("chunk")

                logger.info(
                    f"ID: {passage.id[:16]}... | "
                    f"Existing: [{','.join(tag_coverage)}] | "
                    f"Computed: category={metadata['category']}, "
                    f"quality={metadata['quality']}, "
                    f"reg_align={metadata['reg_align']}"
                )

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze Letta archive passages and compute metadata"
    )
    parser.add_argument(
        "--archive",
        choices=["db1_regulatory", "db2_entity_qms", "all"],
        default="all",
        help="Archive to analyze (default: all)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Run full analysis and generate report"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate passages and show computed metadata"
    )
    parser.add_argument(
        "--letta-url",
        default="http://localhost:8283",
        help="Letta server URL"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10,
        help="Number of passages to analyze/validate"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Output analysis results to JSON file"
    )

    args = parser.parse_args()

    # Default to analyze if no action specified
    if not args.analyze and not args.validate:
        args.analyze = True

    try:
        enricher = PassageEnricher(base_url=args.letta_url)

        if args.analyze:
            if args.archive == "all":
                results = enricher.analyze_all_archives()
            else:
                results = {args.archive: enricher.analyze_archive(args.archive)}

            # Print summary
            print("\n" + "="*60)
            print("PASSAGE ANALYSIS REPORT")
            print("="*60)
            print("\nNOTE: Letta API does not support passage tag updates.")
            print("      Metadata is computed at QUERY TIME by letta_workflow.py")
            print("="*60)

            for archive_name, stats in results.items():
                if "error" in stats:
                    print(f"\n{archive_name}: {stats['error']}")
                    continue

                print(f"\n{archive_name}:")
                print(f"  Archive ID:         {stats.get('archive_id', 'N/A')}")
                print(f"  Passages analyzed:  {stats.get('total_analyzed', 0)}")
                print(f"  Avg Quality Score:  {stats.get('avg_quality', 'N/A')}")
                print(f"  Avg Reg Alignment:  {stats.get('avg_reg_align', 'N/A')}")

                if stats.get("categories"):
                    print(f"\n  Category Distribution:")
                    for cat, count in sorted(stats["categories"].items(), key=lambda x: -x[1]):
                        print(f"    {cat}: {count}")

                if stats.get("years"):
                    print(f"\n  Year Distribution:")
                    for year, count in sorted(stats["years"].items()):
                        print(f"    {year}: {count}")

                if stats.get("existing_tags_analysis"):
                    print(f"\n  Existing Tag Prefixes:")
                    for prefix, count in sorted(stats["existing_tags_analysis"].items(), key=lambda x: -x[1]):
                        print(f"    {prefix}: {count}")

            # Output to JSON if requested
            if args.output_json:
                import json
                # Remove non-serializable items
                for archive_name, stats in results.items():
                    stats.pop("sample_passages", None)
                with open(args.output_json, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"\nResults saved to: {args.output_json}")

        if args.validate:
            if args.archive == "all":
                for archive_name in ["db1_regulatory", "db2_entity_qms"]:
                    enricher.validate_passages(archive_name, sample_size=args.sample_size)
            else:
                enricher.validate_passages(args.archive, sample_size=args.sample_size)

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
