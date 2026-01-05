"""
Visualization Module - Generate comprehensive charts and insights for log analysis

This module provides multiple visualization types for log classification results:
- Category distribution (bar chart)
- Severity analysis (pie chart)
- Source system breakdown
- Timeline analysis (if timestamps available)
- Top error patterns
- Interactive HTML dashboards
"""
import io
import base64
from typing import List, Dict, Optional, Tuple
from collections import Counter
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from severity_mapper import (
    get_severity, get_severity_color, get_severity_icon,
    get_severity_stats, SeverityLevel, SEVERITY_COLORS
)


class LogVisualizer:
    """Generate visualizations for log classification results"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize visualizer with classification results
        
        Args:
            df: DataFrame with columns ['message', 'target_label', 'method', 'confidence']
        """
        self.df = df.copy()
        self._add_severity_info()
    
    def _add_severity_info(self):
        """Add severity information to DataFrame"""
        self.df['severity'] = self.df['target_label'].apply(get_severity)
        self.df['severity_color'] = self.df['severity'].apply(lambda s: get_severity_color(s))
        self.df['severity_icon'] = self.df['severity'].apply(lambda s: get_severity_icon(s))
    
    def get_summary_stats(self) -> Dict:
        """Get comprehensive summary statistics"""
        total = len(self.df)
        categories = self.df['target_label'].value_counts().to_dict()
        methods = self.df['method'].value_counts().to_dict()
        
        # Severity stats
        severity_stats = get_severity_stats(self.df['target_label'].tolist())
        
        # Confidence stats
        avg_confidence = self.df['confidence'].mean()
        low_confidence_count = len(self.df[self.df['confidence'] < 0.7])
        
        stats = {
            "total_logs": total,
            "unique_categories": len(categories),
            "category_distribution": categories,
            "method_distribution": methods,
            "severity_stats": severity_stats,
            "confidence_stats": {
                "average": round(avg_confidence, 4),
                "low_confidence_count": low_confidence_count,
                "low_confidence_percentage": round((low_confidence_count / total) * 100, 2) if total > 0 else 0
            }
        }
        
        return stats
    
    def create_category_bar_chart(self, figsize=(12, 6)) -> str:
        """
        Create bar chart of category distribution
        
        Returns:
            Base64 encoded image string
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        category_counts = self.df['target_label'].value_counts()
        categories = category_counts.index.tolist()
        counts = category_counts.values.tolist()
        
        # Get colors based on severity
        colors = [get_severity_color(get_severity(cat)) for cat in categories]
        
        bars = ax.bar(range(len(categories)), counts, color=colors, edgecolor='black', linewidth=0.5)
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.set_xlabel('Category', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_title('Log Category Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add count labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"
    
    def create_severity_pie_chart(self, figsize=(10, 8)) -> str:
        """
        Create pie chart of severity distribution
        
        Returns:
            Base64 encoded image string
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        severity_counts = self.df['severity'].value_counts()
        labels = [f"{get_severity_icon(SeverityLevel(s))} {s}" for s in severity_counts.index]
        sizes = severity_counts.values.tolist()  # Convert to list for matplotlib compatibility
        colors = [SEVERITY_COLORS[SeverityLevel(s)] for s in severity_counts.index]
        
        # Create pie chart with percentage labels
        pie_result = ax.pie(
            sizes, 
            labels=labels, 
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 11, 'weight': 'bold'}
        )
        
        # Make percentage text more readable
        if len(pie_result) == 3:
            wedges, texts, autotexts = pie_result
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')  # type: ignore
        
        ax.set_title('Severity Distribution', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"
    
    def create_method_distribution_chart(self, figsize=(10, 6)) -> str:
        """
        Create bar chart of classification method distribution
        
        Returns:
            Base64 encoded image string
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        method_counts = self.df['method'].value_counts()
        methods = method_counts.index.tolist()
        counts = method_counts.values.tolist()
        
        colors_map = {
            'regex': '#4CAF50',
            'bert': '#2196F3',
            'llm': '#FF9800'
        }
        colors = [colors_map.get(m.lower(), '#9E9E9E') for m in methods]
        
        bars = ax.bar(methods, counts, color=colors, edgecolor='black', linewidth=0.5)
        ax.set_xlabel('Classification Method', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_title('Classification Method Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add count labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"
    
    def create_confidence_distribution(self, figsize=(10, 6)) -> str:
        """
        Create histogram of confidence scores
        
        Returns:
            Base64 encoded image string
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create histogram
        n, bins, patches = ax.hist(
            self.df['confidence'], 
            bins=20, 
            color='#3498db', 
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7
        )
        
        # Color code bins by confidence level
        if hasattr(patches, '__iter__'):
            for i, patch in enumerate(patches):  # type: ignore
                if bins[i] < 0.5:
                    patch.set_facecolor('#e74c3c')  # Red for low confidence
                elif bins[i] < 0.7:
                    patch.set_facecolor('#f39c12')  # Orange for medium
                else:
                    patch.set_facecolor('#2ecc71')  # Green for high
        
        ax.set_xlabel('Confidence Score', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title('Classification Confidence Distribution', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Add vertical line for average
        avg_conf = self.df['confidence'].mean()
        ax.axvline(avg_conf, color='red', linestyle='--', linewidth=2, 
                   label=f'Average: {avg_conf:.3f}')
        ax.legend()
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return f"data:image/png;base64,{img_base64}"
    
    def create_interactive_dashboard(self) -> str:
        """
        Create interactive Plotly dashboard with multiple charts
        
        Returns:
            HTML string with embedded Plotly charts
        """
        # Create subplot figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Category Distribution',
                'Severity Breakdown',
                'Classification Methods',
                'Confidence Distribution'
            ),
            specs=[
                [{"type": "bar"}, {"type": "pie"}],
                [{"type": "bar"}, {"type": "histogram"}]
            ]
        )
        
        # 1. Category distribution
        category_counts = self.df['target_label'].value_counts()
        colors_cat = [get_severity_color(get_severity(cat)) for cat in category_counts.index]
        fig.add_trace(
            go.Bar(
                x=category_counts.index.tolist(),
                y=category_counts.values.tolist(),
                marker_color=colors_cat,
                name='Categories',
                showlegend=False,
                text=category_counts.values.tolist(),
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # 2. Severity pie chart
        severity_counts = self.df['severity'].value_counts()
        severity_labels = [f"{get_severity_icon(SeverityLevel(s))} {s}" 
                          for s in severity_counts.index]
        severity_colors = [SEVERITY_COLORS[SeverityLevel(s)] for s in severity_counts.index]
        fig.add_trace(
            go.Pie(
                labels=severity_labels,
                values=severity_counts.values.tolist(),
                marker_colors=severity_colors,
                name='Severity',
                textinfo='label+percent',
                showlegend=False
            ),
            row=1, col=2
        )
        
        # 3. Method distribution
        method_counts = self.df['method'].value_counts()
        method_colors_map = {'regex': '#4CAF50', 'bert': '#2196F3', 'llm': '#FF9800'}
        method_colors = [method_colors_map.get(m.lower(), '#9E9E9E') 
                        for m in method_counts.index]
        fig.add_trace(
            go.Bar(
                x=method_counts.index.tolist(),
                y=method_counts.values.tolist(),
                marker_color=method_colors,
                name='Methods',
                showlegend=False,
                text=method_counts.values.tolist(),
                textposition='outside'
            ),
            row=2, col=1
        )
        
        # 4. Confidence histogram
        fig.add_trace(
            go.Histogram(
                x=self.df['confidence'],
                nbinsx=20,
                marker_color='#3498db',
                name='Confidence',
                showlegend=False
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text="Log Classification Dashboard",
            title_font_size=20,
            showlegend=False
        )
        
        # Update axes
        fig.update_xaxes(title_text="Category", row=1, col=1, tickangle=-45)
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_xaxes(title_text="Method", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        fig.update_xaxes(title_text="Confidence", row=2, col=2)
        fig.update_yaxes(title_text="Frequency", row=2, col=2)
        
        return fig.to_html(include_plotlyjs='cdn', full_html=False)
    
    def create_top_patterns_table(self, top_n: int = 10) -> List[Dict]:
        """
        Extract top log patterns by category
        
        Args:
            top_n: Number of top patterns per category
            
        Returns:
            List of dictionaries with pattern information
        """
        patterns = []
        
        for category in self.df['target_label'].unique():
            cat_df = self.df[self.df['target_label'] == category]
            
            # Get most common messages (patterns)
            message_counts = cat_df['message'].value_counts().head(top_n)
            
            for message, count in message_counts.items():
                avg_conf = cat_df[cat_df['message'] == message]['confidence'].mean()
                severity = get_severity(category)
                
                patterns.append({
                    'category': category,
                    'severity': severity.value,
                    'icon': get_severity_icon(severity),
                    'pattern': message[:100] + '...' if len(message) > 100 else message,
                    'count': int(count),
                    'avg_confidence': round(avg_conf, 4)
                })
        
        # Sort by severity priority then count
        patterns.sort(key=lambda x: (-self._severity_sort_key(x['severity']), -x['count']))
        
        return patterns[:top_n * 3]  # Return top patterns across all categories
    
    def _severity_sort_key(self, severity_str: str) -> int:
        """Convert severity string to sort key"""
        order = {'CRITICAL': 5, 'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'INFO': 1}
        return order.get(severity_str, 0)
    
    def generate_all_visualizations(self) -> Dict:
        """
        Generate all visualizations and return as dictionary
        
        Returns:
            Dictionary with all visualization data
        """
        return {
            'summary_stats': self.get_summary_stats(),
            'category_chart': self.create_category_bar_chart(),
            'severity_chart': self.create_severity_pie_chart(),
            'method_chart': self.create_method_distribution_chart(),
            'confidence_chart': self.create_confidence_distribution(),
            'interactive_dashboard': self.create_interactive_dashboard(),
            'top_patterns': self.create_top_patterns_table()
        }
    
    def export_insights_report(self) -> str:
        """
        Generate text-based insights report
        
        Returns:
            Formatted insights string
        """
        stats = self.get_summary_stats()
        
        report = []
        report.append("=" * 80)
        report.append("LOG CLASSIFICATION INSIGHTS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Overall stats
        report.append(f"Total Logs Analyzed: {stats['total_logs']}")
        report.append(f"Unique Categories: {stats['unique_categories']}")
        report.append(f"Average Confidence: {stats['confidence_stats']['average']:.2%}")
        report.append("")
        
        # Severity analysis
        sev_stats = stats['severity_stats']
        report.append("SEVERITY ANALYSIS:")
        report.append("-" * 80)
        for severity, count in sev_stats['severity_counts'].items():
            pct = sev_stats['severity_percentages'][severity]
            icon = get_severity_icon(SeverityLevel(severity))
            report.append(f"{icon} {severity:10s}: {count:5d} logs ({pct:5.1f}%)")
        report.append("")
        report.append(f"⚠️  Critical Logs: {sev_stats['critical_count']}")
        report.append(f"⚠️  High Priority: {sev_stats['high_priority_count']}")
        report.append(f"⚠️  Requires Attention: {sev_stats['requires_attention']}")
        report.append("")
        
        # Category breakdown
        report.append("CATEGORY BREAKDOWN:")
        report.append("-" * 80)
        for category, count in sorted(
            stats['category_distribution'].items(), 
            key=lambda x: x[1], 
            reverse=True
        ):
            pct = (count / stats['total_logs']) * 100
            severity = get_severity(category)
            icon = get_severity_icon(severity)
            report.append(f"{icon} {category:30s}: {count:5d} ({pct:5.1f}%)")
        report.append("")
        
        # Method distribution
        report.append("CLASSIFICATION METHOD DISTRIBUTION:")
        report.append("-" * 80)
        for method, count in stats['method_distribution'].items():
            pct = (count / stats['total_logs']) * 100
            report.append(f"{method:10s}: {count:5d} ({pct:5.1f}%)")
        report.append("")
        
        # Confidence analysis
        report.append("CONFIDENCE ANALYSIS:")
        report.append("-" * 80)
        conf_stats = stats['confidence_stats']
        report.append(f"Average Confidence: {conf_stats['average']:.2%}")
        report.append(f"Low Confidence (<70%): {conf_stats['low_confidence_count']} logs "
                     f"({conf_stats['low_confidence_percentage']:.1f}%)")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def create_visualizations(df: pd.DataFrame) -> Dict:
    """
    Convenience function to generate all visualizations
    
    Args:
        df: DataFrame with classification results
        
    Returns:
        Dictionary with all visualization data
    """
    visualizer = LogVisualizer(df)
    return visualizer.generate_all_visualizations()


def create_insights_report(df: pd.DataFrame) -> str:
    """
    Convenience function to generate insights report
    
    Args:
        df: DataFrame with classification results
        
    Returns:
        Formatted insights string
    """
    visualizer = LogVisualizer(df)
    return visualizer.export_insights_report()


if __name__ == "__main__":
    # Test with sample data
    print("Testing visualization module...")
    
    sample_data = {
        'message': [
            'Database connection failed',
            'User login successful',
            'Security breach detected',
            'API response time: 250ms',
            'Memory usage at 85%',
        ] * 10,
        'target_label': [
            'Critical Error',
            'User Action',
            'Security Alert',
            'HTTP Status',
            'Resource Usage',
        ] * 10,
        'method': ['bert'] * 50,
        'confidence': [0.95] * 50
    }
    
    df = pd.DataFrame(sample_data)
    
    visualizer = LogVisualizer(df)
    stats = visualizer.get_summary_stats()
    
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total Logs: {stats['total_logs']}")
    print(f"Unique Categories: {stats['unique_categories']}")
    print(f"\nCategory Distribution: {stats['category_distribution']}")
    print(f"\nSeverity Stats: {stats['severity_stats']}")
    
    print("\n" + visualizer.export_insights_report())
    
    print("\n✅ Visualization module test complete!")
