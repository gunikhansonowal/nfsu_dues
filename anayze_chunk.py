#!/usr/bin/env python3
"""
DUES Chunk Storage Analyzer
Analyzes chunk files in the BLOBS directory of DUES forensics tool
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
from dataclasses import dataclass
from datetime import datetime
import statistics

@dataclass
class ChunkInfo:
    """Information about a stored chunk"""
    filename: str
    size: int
    sha256_hash: str
    path: Path
    modification_time: datetime
    first_bytes: bytes  # First 16 bytes for quick comparison
    
@dataclass
class AnalysisResults:
    """Results of chunk analysis"""
    total_chunks: int = 0
    total_size: int = 0
    average_size: float = 0.0
    median_size: float = 0.0
    size_distribution: Dict[str, int] = None
    potential_duplicates: List[Tuple[str, str]] = None
    corrupted_chunks: List[str] = None
    chunk_references: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.size_distribution is None:
            self.size_distribution = {}
        if self.potential_duplicates is None:
            self.potential_duplicates = []
        if self.corrupted_chunks is None:
            self.corrupted_chunks = []
        if self.chunk_references is None:
            self.chunk_references = {}

class DuesChunkAnalyzer:
    """Analyzes DUES chunk storage in BLOBS directory"""
    
    # Common chunk size categories (based on 256KB default)
    CHUNK_CATEGORIES = {
        'tiny': (0, 1024),           # < 1KB
        'small': (1024, 10240),      # 1KB - 10KB
        'medium': (10240, 102400),   # 10KB - 100KB
        'large': (102400, 262144),   # 100KB - 256KB
        'oversized': (262144, float('inf'))  # > 256KB
    }
    
    def __init__(self, blobs_path: str):
        """
        Initialize analyzer with path to BLOBS directory
        
        Args:
            blobs_path: Path to /home/guni/ISEA_Project/indicer/Carp/BLOBS
        """
        self.blobs_path = Path(blobs_path)
        self.chunks: Dict[str, ChunkInfo] = {}
        self.results = AnalysisResults()
        
        # Validate path
        if not self.blobs_path.exists():
            raise FileNotFoundError(f"BLOBS directory not found: {blobs_path}")
        if not self.blobs_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {blobs_path}")
    
    def scan_chunks(self) -> AnalysisResults:
        """
        Scan all chunk files in BLOBS directory
        
        Returns:
            AnalysisResults object with scan results
        """
        print(f"Scanning BLOBS directory: {self.blobs_path}")
        print("-" * 60)
        
        # Get all .blob files
        blob_files = list(self.blobs_path.glob("*.blob"))
        
        if not blob_files:
            print(" No .blob files found in directory!")
            return self.results
        
        print(f" Found {len(blob_files)} chunk files")
        
        # Process each chunk file
        for i, blob_file in enumerate(blob_files, 1):
            try:
                chunk_info = self._analyze_chunk(blob_file)
                self.chunks[chunk_info.filename] = chunk_info
                
                # Progress indicator
                if i % 100 == 0 or i == len(blob_files):
                    print(f"  Processed {i}/{len(blob_files)} files...")
                    
            except Exception as e:
                print(f"Error processing {blob_file.name}: {e}")
                self.results.corrupted_chunks.append(str(blob_file))
        
        # Calculate statistics
        self._calculate_statistics()
        
        # Find potential duplicates
        self._find_potential_duplicates()
        
        return self.results
    
    def _analyze_chunk(self, blob_file: Path) -> ChunkInfo:
        """
        Analyze a single chunk file
        
        Args:
            blob_file: Path to the .blob file
            
        Returns:
            ChunkInfo object with file details
        """
        # Get file stats
        stat = blob_file.stat()
        
        # Read file content for analysis
        with open(blob_file, 'rb') as f:
            content = f.read()
        
        # Calculate SHA256 hash
        sha256_hash = hashlib.sha256(content).hexdigest()
        
        # Get first 16 bytes for quick comparison
        first_bytes = content[:16] if len(content) >= 16 else content
        
        return ChunkInfo(
            filename=blob_file.name,
            size=stat.st_size,
            sha256_hash=sha256_hash,
            path=blob_file,
            modification_time=datetime.fromtimestamp(stat.st_mtime),
            first_bytes=first_bytes
        )
    
    def _calculate_statistics(self):
        """Calculate statistics from scanned chunks"""
        if not self.chunks:
            return
        
        sizes = [chunk.size for chunk in self.chunks.values()]
        
        self.results.total_chunks = len(self.chunks)
        self.results.total_size = sum(sizes)
        self.results.average_size = statistics.mean(sizes) if sizes else 0
        self.results.median_size = statistics.median(sizes) if sizes else 0
        
        # Categorize by size
        for chunk in self.chunks.values():
            category = self._categorize_size(chunk.size)
            self.results.size_distribution[category] = \
                self.results.size_distribution.get(category, 0) + 1
    
    def _categorize_size(self, size: int) -> str:
        """
        Categorize chunk by size
        
        Args:
            size: Chunk size in bytes
            
        Returns:
            Size category name
        """
        for category, (min_size, max_size) in self.CHUNK_CATEGORIES.items():
            if min_size <= size < max_size:
                return category
        return 'unknown'
    
    def _find_potential_duplicates(self):
        """Find chunks with identical content (potential duplicates)"""
        if not self.chunks:
            return
        
        # Group by hash to find duplicates
        hash_groups: Dict[str, List[str]] = {}
        
        for filename, chunk_info in self.chunks.items():
            hash_groups.setdefault(chunk_info.sha256_hash, []).append(filename)
        
        # Find groups with more than one file (duplicates)
        for hash_value, filenames in hash_groups.items():
            if len(filenames) > 1:
                # These are exact duplicates
                for i in range(len(filenames)):
                    for j in range(i + 1, len(filenames)):
                        self.results.potential_duplicates.append(
                            (filenames[i], filenames[j])
                        )
    
    def find_chunk_by_hash(self, target_hash: str) -> Optional[ChunkInfo]:
        """
        Find a chunk by its SHA256 hash
        
        Args:
            target_hash: SHA256 hash to search for
            
        Returns:
            ChunkInfo if found, None otherwise
        """
        for chunk_info in self.chunks.values():
            if chunk_info.sha256_hash == target_hash:
                return chunk_info
        return None
    
    def get_size_histogram(self) -> Dict[str, int]:
        """
        Get detailed size histogram
        
        Returns:
            Dictionary with size ranges and counts
        """
        histogram = {}
        if not self.chunks:
            return histogram
        
        # Define size bins (in KB)
        bins = [0, 64, 128, 192, 256, 512, 1024, 2048, 4096, float('inf')]
        bin_labels = ['0-64K', '64-128K', '128-192K', '192-256K', 
                      '256-512K', '512K-1M', '1-2M', '2-4M', '4M+']
        
        for chunk in self.chunks.values():
            size_kb = chunk.size / 1024
            for i, bin_max in enumerate(bins[:-1]):
                if bins[i] <= size_kb < bins[i + 1]:
                    histogram[bin_labels[i]] = histogram.get(bin_labels[i], 0) + 1
                    break
        
        return histogram
    
    def verify_chunk_integrity(self, chunk_name: str) -> Tuple[bool, str]:
        """
        Verify the integrity of a specific chunk
        
        Args:
            chunk_name: Name of the chunk file
            
        Returns:
            Tuple of (is_valid, message)
        """
        if chunk_name not in self.chunks:
            return False, f"Chunk not found: {chunk_name}"
        
        chunk = self.chunks[chunk_name]
        
        try:
            # Re-read and verify hash
            with open(chunk.path, 'rb') as f:
                content = f.read()
            
            current_hash = hashlib.sha256(content).hexdigest()
            
            if current_hash == chunk.sha256_hash:
                return True, f" Chunk integrity verified: {chunk_name}"
            else:
                return False, f" Hash mismatch detected: {chunk_name}"
                
        except Exception as e:
            return False, f" Error reading chunk: {chunk_name} - {e}"
    
    def export_to_json(self, output_path: str):
        """
        Export analysis results to JSON file
        
        Args:
            output_path: Path to output JSON file
        """
        export_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'blobs_directory': str(self.blobs_path),
            'total_chunks': self.results.total_chunks,
            'total_size_bytes': self.results.total_size,
            'total_size_mb': self.results.total_size / (1024 * 1024),
            'average_size_bytes': self.results.average_size,
            'median_size_bytes': self.results.median_size,
            'size_distribution': self.results.size_distribution,
            'size_histogram': self.get_size_histogram(),
            'potential_duplicates_count': len(self.results.potential_duplicates),
            'potential_duplicates': self.results.potential_duplicates,
            'corrupted_chunks': self.results.corrupted_chunks,
            'chunk_details': {
                name: {
                    'size': chunk.size,
                    'sha256': chunk.sha256_hash,
                    'path': str(chunk.path),
                    'modified': chunk.modification_time.isoformat(),
                    'first_bytes_hex': chunk.first_bytes.hex()
                }
                for name, chunk in self.chunks.items()
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f" Results exported to: {output_path}")
    
    def print_summary(self):
        """Print a summary of the analysis"""
        if not self.chunks:
            print("No chunks to analyze")
            return
        
        print("\n" + "="*60)
        print(" DUES CHUNK STORAGE ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\n Directory: {self.blobs_path}")
        print(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\nBasic Statistics:")
        print(f"   • Total chunks: {self.results.total_chunks:,}")
        print(f"   • Total size: {self.results.total_size / (1024*1024):.2f} MB")
        print(f"   • Average chunk size: {self.results.average_size / 1024:.2f} KB")
        print(f"   • Median chunk size: {self.results.median_size / 1024:.2f} KB")
        
        print(f"\nSize Distribution:")
        for category, count in self.results.size_distribution.items():
            percentage = (count / self.results.total_chunks) * 100
            print(f"   • {category.title()}: {count:,} chunks ({percentage:.1f}%)")
        
        print(f"\n Duplicate Detection:")
        duplicate_count = len(self.results.potential_duplicates)
        if duplicate_count > 0:
            print(f"    Found {duplicate_count} potential duplicate pairs")
            print(f"    This suggests {duplicate_count * 2} chunks could be deduplicated")
        else:
            print(f"   No exact duplicates found (good deduplication)")
        
        if self.results.corrupted_chunks:
            print(f"\n Corrupted Chunks: {len(self.results.corrupted_chunks)}")
            for corrupted in self.results.corrupted_chunks[:5]:  # Show first 5
                print(f"   • {Path(corrupted).name}")
            if len(self.results.corrupted_chunks) > 5:
                print(f"   • ... and {len(self.results.corrupted_chunks) - 5} more")
        
        print(f"\nStorage Efficiency:")
        unique_chunks = len(set(chunk.sha256_hash for chunk in self.chunks.values()))
        dedup_ratio = self.results.total_chunks / unique_chunks if unique_chunks > 0 else 1
        print(f"   • Unique chunks: {unique_chunks:,}")
        print(f"   • Deduplication ratio: {dedup_ratio:.2f}:1")
        print(f"   • Space savings: {(1 - (1/dedup_ratio)) * 100:.1f}%")
        
        print("\n" + "="*60)

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Analyze DUES chunk storage in BLOBS directory'
    )
    parser.add_argument(
        'blobs_path',
        help='Path to BLOBS directory (e.g., /home/guni/ISEA_Project/indicer/Carp/BLOBS)'
    )
    parser.add_argument(
        '--export', '-e',
        help='Export results to JSON file'
    )
    parser.add_argument(
        '--verify', '-v',
        help='Verify integrity of specific chunk file'
    )
    parser.add_argument(
        '--find-hash', '-f',
        help='Find chunk by SHA256 hash'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = DuesChunkAnalyzer(args.blobs_path)
        
        # Check specific operations
        if args.verify:
            if not args.quiet:
                print(f"Verifying chunk: {args.verify}")
            result, message = analyzer.verify_chunk_integrity(args.verify)
            print(message)
            return
        
        if args.find_hash:
            if not args.quiet:
                print(f"🔍 Searching for hash: {args.find_hash}")
            chunk = analyzer.find_chunk_by_hash(args.find_hash)
            if chunk:
                print(f" Found chunk: {chunk.filename}")
                print(f"   Size: {chunk.size:,} bytes")
                print(f"   Path: {chunk.path}")
                print(f"   Modified: {chunk.modification_time}")
            else:
                print(f"No chunk found with hash: {args.find_hash}")
            return
        
        # Perform full analysis
        results = analyzer.scan_chunks()
        
        if not args.quiet:
            analyzer.print_summary()
        
        # Export if requested
        if args.export:
            analyzer.export_to_json(args.export)
        
        # Interactive mode if no export
        elif not args.quiet and results.total_chunks > 0:
            print("\nTip: Use --export to save detailed results")
            print("Tip: Use --verify <chunk_name> to check specific chunk integrity")
            print(" Tip: Use --find-hash <sha256> to locate a specific chunk")
        
    except Exception as e:
        print(f" Error: {e}")
        return 1
    
    return 0

# Example usage functions for direct Python execution
def example_usage():
    """Example usage of the analyzer"""
    blobs_path = "/home/guni/ISEA_Project/indicer/Carp/BLOBS"
    
    try:
        # Create analyzer
        analyzer = DuesChunkAnalyzer(blobs_path)
        
        # Scan all chunks
        print("Starting chunk analysis...")
        results = analyzer.scan_chunks()
        
        # Print summary
        analyzer.print_summary()
        
        # Export to JSON
        analyzer.export_to_json("dues_chunk_analysis.json")
        
        # Example: Find a chunk by hash
        if results.total_chunks > 0:
            sample_chunk = list(analyzer.chunks.values())[0]
            print(f"\n🔍 Looking for chunk with hash: {sample_chunk.sha256_hash}")
            found = analyzer.find_chunk_by_hash(sample_chunk.sha256_hash)
            if found:
                print(f"Found: {found.filename}")
        
        # Example: Check integrity
        if results.total_chunks > 0:
            sample_name = list(analyzer.chunks.keys())[0]
            print(f"\nVerifying integrity of: {sample_name}")
            is_valid, message = analyzer.verify_chunk_integrity(sample_name)
            print(message)
        
        # Show histogram
        histogram = analyzer.get_size_histogram()
        print(f"\nSize histogram:")
        for size_range, count in histogram.items():
            print(f"   {size_range}: {count:,} chunks")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # For direct script execution
    # example_usage()  # Uncomment to test
    
    # For command-line usage
    import sys
    sys.exit(main())
