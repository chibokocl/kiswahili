"""
Result formatting utilities for the Ki-Micheweni grammar engine.
"""

from typing import Dict, Any, List
import json


class ResultFormatter:
    """Formats analysis results for different output types."""
    
    @staticmethod
    def format_for_json(result: Dict[str, Any]) -> str:
        """Format result as JSON string."""
        # Convert dataclasses and enums to dictionaries
        formatted = ResultFormatter._serialize_for_json(result)
        return json.dumps(formatted, indent=2, ensure_ascii=False)
    
    @staticmethod
    def format_for_terminal(result: Dict[str, Any]) -> str:
        """Format result for terminal display with colors and formatting."""
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        output = []
        
        # Header
        output.append("🔍 Ki-Micheweni Grammar Analysis")
        output.append("=" * 50)
        output.append(f"Sentence: '{result['original']}'")
        output.append(f"Type: {result['sentence_type']}")
        output.append("")
        
        # Structure
        if result.get('structure', {}).get('explanation'):
            output.append("📐 Structure:")
            output.append(f"  {result['structure']['explanation'][0]}")
            output.append("")
        
        # Token analysis
        output.append("🔤 Token Analysis:")
        for token in result.get('tokens', []):
            output.append(f"  • {token['word']} ({token['syntactic_role']})")
            
            if token.get('ngeli_analysis'):
                nga = token['ngeli_analysis']
                output.append(f"    └─ Ngeli: {nga['ngeli']} ({nga['number']})")
                if nga['semantic_function'] != 'neutral':
                    output.append(f"    └─ Function: {nga['semantic_function']}")
        
        output.append("")
        
        # Agreement
        agreement = result.get('agreement', {})
        if hasattr(agreement, 'issues') and agreement.issues:
            output.append("⚠️  Agreement Issues:")
            for issue in agreement.issues:
                output.append(f"  • {issue}")
        else:
            output.append("✅ Agreement: All correct")
        
        output.append("")
        
        # Migrations
        if result.get('ngeli_migrations'):
            output.append("🔄 Ngeli Migrations:")
            for migration in result['ngeli_migrations']:
                mig = migration['migration']
                output.append(f"  • {migration['word']}: {mig['canonical_ngeli']} → {mig['current_ngeli']}")
                output.append(f"    └─ {mig['reason']}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_summary(result: Dict[str, Any]) -> str:
        """Format a brief summary of the analysis."""
        if "error" in result:
            return f"Error: {result['error']}"
        
        summary = []
        summary.append(f"Sentence: {result['original']}")
        summary.append(f"Type: {result['sentence_type']}")
        
        # Count ngeli classes used
        sem = result.get('semantic_analysis', {})
        ngeli_count = len(sem.get('ngeli_distribution', {}))
        summary.append(f"Ngeli classes: {ngeli_count}/18")
        
        # Agreement status
        agreement = result.get('agreement', {})
        if hasattr(agreement, 'issues') and agreement.issues:
            summary.append("Agreement: ⚠️  Issues detected")
        else:
            summary.append("Agreement: ✅ Correct")
        
        # Migrations
        migration_count = len(result.get('ngeli_migrations', []))
        if migration_count > 0:
            summary.append(f"Migrations: {migration_count} detected")
        
        return " | ".join(summary)
    
    @staticmethod
    def format_word_analysis(word_result: Dict[str, Any]) -> str:
        """Format single word analysis result."""
        output = []
        output.append(f"🔤 Word Analysis: '{word_result['word']}'")
        output.append("-" * 30)
        
        ngeli_info = word_result.get('ngeli_analysis')
        if ngeli_info:
            output.append(f"Ngeli: {ngeli_info.ngeli_class} ({ngeli_info.number})")
            output.append(f"Confidence: {ngeli_info.confidence:.2f}")
            output.append(f"Semantic function: {ngeli_info.semantic_function.value}")
            
            morph = ngeli_info.morphological_analysis
            if morph.get('prefix') and morph.get('root'):
                output.append(f"Morphology: {morph['prefix']} + {morph['root']}")
            
            if morph.get('phonological_changes'):
                output.append("Phonological processes:")
                for process in morph['phonological_changes']:
                    output.append(f"  • {process}")
        
        migration = word_result.get('migration_analysis')
        if migration and migration.get('migration_detected'):
            output.append("")
            output.append("🔄 Migration detected:")
            output.append(f"  {migration['canonical_ngeli']} → {migration['current_ngeli']}")
            output.append(f"  Reason: {migration['reason']}")
        
        return "\n".join(output)
    
    @staticmethod
    def _serialize_for_json(obj: Any) -> Any:
        """Recursively serialize objects for JSON output."""
        if hasattr(obj, '__dict__'):
            # Handle dataclasses and custom objects
            return {k: ResultFormatter._serialize_for_json(v) for k, v in obj.__dict__.items()}
        elif hasattr(obj, 'value'):
            # Handle enums
            return obj.value
        elif isinstance(obj, dict):
            return {k: ResultFormatter._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [ResultFormatter._serialize_for_json(item) for item in obj]
        else:
            return obj
    
    @staticmethod
    def format_comparison(results: List[Dict[str, Any]]) -> str:
        """Format comparison of multiple analysis results."""
        if not results:
            return "No results to compare"
        
        output = []
        output.append("📊 Analysis Comparison")
        output.append("=" * 40)
        
        for i, result in enumerate(results, 1):
            output.append(f"\n{i}. {result.get('original', 'Unknown sentence')}")
            output.append(f"   Type: {result.get('sentence_type', 'Unknown')}")
            
            sem = result.get('semantic_analysis', {})
            ngeli_count = len(sem.get('ngeli_distribution', {}))
            output.append(f"   Ngeli complexity: {ngeli_count}/18")
            
            migration_count = len(result.get('ngeli_migrations', []))
            if migration_count > 0:
                output.append(f"   Migrations: {migration_count}")
        
        return "\n".join(output)