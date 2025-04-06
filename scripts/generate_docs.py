#!/usr/bin/env python3
"""
Documentation generator for Skin Wellness Navigator.
Generates API documentation, usage guides, and developer documentation.
"""

import os
import sys
import json
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/docs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocGenerator:
    """Handles documentation generation."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.docs_dir = self.project_root / 'docs'
        self.api_docs_dir = self.docs_dir / 'api'
        self.guides_dir = self.docs_dir / 'guides'
        
        # Create documentation directories
        for directory in [self.docs_dir, self.api_docs_dir, self.guides_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def generate_api_docs(self):
        """Generate API documentation from source code."""
        try:
            # Import server module
            sys.path.insert(0, str(self.project_root))
            import server
            
            # Extract route information
            routes = []
            for rule in server.app.url_map.iter_rules():
                if rule.endpoint != 'static':
                    view_func = server.app.view_functions[rule.endpoint]
                    doc = inspect.getdoc(view_func) or "No documentation available"
                    
                    routes.append({
                        'endpoint': rule.endpoint,
                        'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                        'url': str(rule),
                        'description': doc,
                        'parameters': self._extract_parameters(view_func)
                    })
            
            # Generate API documentation
            api_doc = self._generate_api_markdown(routes)
            
            # Save documentation
            api_doc_path = self.api_docs_dir / 'api_reference.md'
            api_doc_path.write_text(api_doc)
            
            logger.info(f"API documentation generated: {api_doc_path}")
            
        except Exception as e:
            logger.error(f"Error generating API documentation: {e}")
            raise

    def _extract_parameters(self, func) -> List[Dict]:
        """Extract function parameters and their types."""
        params = []
        sig = inspect.signature(func)
        
        for name, param in sig.parameters.items():
            if name != 'self':
                param_info = {
                    'name': name,
                    'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                    'default': str(param.default) if param.default != inspect.Parameter.empty else None,
                    'required': param.default == inspect.Parameter.empty
                }
                params.append(param_info)
        
        return params

    def _generate_api_markdown(self, routes: List[Dict]) -> str:
        """Generate markdown documentation for API routes."""
        doc = "# API Reference\n\n"
        doc += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for route in routes:
            doc += f"## {route['endpoint']}\n\n"
            doc += f"**URL:** `{route['url']}`\n\n"
            doc += f"**Methods:** {', '.join(route['methods'])}\n\n"
            doc += "**Description:**\n\n"
            doc += f"{route['description']}\n\n"
            
            if route['parameters']:
                doc += "**Parameters:**\n\n"
                doc += "| Name | Type | Required | Default | Description |\n"
                doc += "|------|------|----------|---------|-------------|\n"
                
                for param in route['parameters']:
                    doc += f"| {param['name']} | {param['type']} | "
                    doc += f"{'Yes' if param['required'] else 'No'} | "
                    doc += f"{param['default'] or '-'} | - |\n"
                
                doc += "\n"
            
            doc += "---\n\n"
        
        return doc

    def generate_user_guide(self):
        """Generate user guide documentation."""
        guide = """# Skin Wellness Navigator User Guide

## Introduction

The Skin Wellness Navigator is a comprehensive tool for analyzing skin conditions and providing health insights.

## Features

1. **Image Analysis**
   - Upload skin images for analysis
   - Receive detailed analysis results
   - View similar cases and statistics

2. **Clinical Data Integration**
   - Access comprehensive clinical data
   - Compare with similar cases
   - Track historical data

3. **Health Recommendations**
   - Receive personalized recommendations
   - Follow-up suggestions
   - Prevention guidelines

## Getting Started

1. **Installation**
   ```bash
   git clone https://github.com/yourusername/skin-wellness-navigator.git
   cd skin-wellness-navigator
   pip install -r requirements.txt
   ```

2. **Configuration**
   - Copy `.env.example` to `.env`
   - Set up your environment variables
   - Configure API keys and database settings

3. **Running the Application**
   ```bash
   python server.py
   ```

## Usage Guide

### Image Analysis

1. Navigate to the image analysis page
2. Upload a clear image of the skin condition
3. Wait for the analysis to complete
4. Review the results and recommendations

### Clinical Data

1. Access the clinical data section
2. Enter relevant search criteria
3. View matching cases and statistics
4. Export data for further analysis

### User Account

1. Create a user account
2. Log in to access all features
3. Manage your profile and preferences
4. Track your analysis history

## Best Practices

1. **Image Quality**
   - Use good lighting
   - Keep the camera steady
   - Focus on the area of concern
   - Include surrounding healthy skin

2. **Data Management**
   - Regularly backup your data
   - Keep track of analysis dates
   - Document any changes

3. **Security**
   - Use strong passwords
   - Enable two-factor authentication
   - Keep your API keys secure

## Troubleshooting

Common issues and their solutions:

1. **Image Upload Fails**
   - Check file size and format
   - Ensure stable internet connection
   - Try reducing image resolution

2. **Analysis Errors**
   - Verify image quality
   - Check system requirements
   - Contact support if persistent

3. **Database Issues**
   - Verify database connection
   - Check permissions
   - Ensure sufficient storage

## Support

For additional support:

- Email: support@skinwellnessnavigator.com
- Documentation: https://docs.skinwellnessnavigator.com
- GitHub Issues: https://github.com/yourusername/skin-wellness-navigator/issues

## Updates and Maintenance

1. **Keeping Up to Date**
   - Regular system updates
   - Security patches
   - Feature enhancements

2. **Backup Procedures**
   - Database backups
   - Configuration backups
   - User data protection

## Contributing

We welcome contributions! Please see our contributing guidelines for more information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
"""
        
        guide_path = self.guides_dir / 'user_guide.md'
        guide_path.write_text(guide)
        logger.info(f"User guide generated: {guide_path}")

    def generate_developer_docs(self):
        """Generate developer documentation."""
        dev_doc = """# Developer Documentation

## Architecture Overview

The Skin Wellness Navigator follows a modular architecture:

1. **Core Components**
   - Web Server (Flask)
   - Database Layer
   - Image Processing
   - AI/ML Models
   - Security Module

2. **Directory Structure**
   ```
   skin-wellness-navigator/
   ├── server.py           # Main application entry
   ├── config.py           # Configuration management
   ├── requirements.txt    # Dependencies
   ├── scripts/           # Utility scripts
   ├── tests/            # Test suite
   ├── docs/             # Documentation
   └── templates/        # Frontend templates
   ```

## Development Setup

1. **Environment Setup**
   ```bash
   python scripts/setup_dev_env.py
   ```

2. **Database Setup**
   ```bash
   python scripts/manage_db.py init
   python scripts/manage_db.py migrate
   ```

3. **Running Tests**
   ```bash
   python run_tests.py
   ```

## Code Style Guide

1. **Python Style**
   - Follow PEP 8
   - Use type hints
   - Document functions and classes
   - Keep functions focused and small

2. **Documentation**
   - Document all public APIs
   - Include usage examples
   - Keep documentation up to date
   - Use clear, concise language

3. **Testing**
   - Write unit tests for new features
   - Maintain test coverage
   - Test edge cases
   - Document test scenarios

## API Development

1. **Adding New Endpoints**
   - Follow RESTful principles
   - Document with docstrings
   - Include request/response examples
   - Add appropriate tests

2. **Security Considerations**
   - Validate all inputs
   - Use proper authentication
   - Follow security best practices
   - Log security events

## Database Management

1. **Migrations**
   - Create clear migration scripts
   - Test migrations thoroughly
   - Include rollback procedures
   - Document schema changes

2. **Performance**
   - Optimize queries
   - Use appropriate indexes
   - Monitor query performance
   - Regular maintenance

## Deployment

1. **Production Setup**
   ```bash
   python scripts/deploy.py --env production
   ```

2. **Monitoring**
   ```bash
   python scripts/monitor.py
   ```

## Contributing Guidelines

1. **Pull Requests**
   - Fork the repository
   - Create feature branch
   - Follow code style
   - Include tests
   - Update documentation

2. **Code Review**
   - Review guidelines
   - Testing requirements
   - Documentation updates
   - Performance considerations

## Security Guidelines

1. **Authentication**
   - Use secure password storage
   - Implement rate limiting
   - Session management
   - Access control

2. **Data Protection**
   - Encrypt sensitive data
   - Secure file handling
   - Input validation
   - Output sanitization

## Performance Optimization

1. **Application Performance**
   - Caching strategies
   - Database optimization
   - Image processing
   - API response times

2. **Monitoring**
   - System metrics
   - Error tracking
   - Performance metrics
   - User analytics

## Troubleshooting

Common development issues and solutions:

1. **Environment Issues**
   - Virtual environment setup
   - Dependency conflicts
   - Path issues
   - Configuration problems

2. **Database Issues**
   - Connection problems
   - Migration errors
   - Query performance
   - Data integrity

## Support Resources

- GitHub Repository
- Issue Tracker
- Development Wiki
- Team Communication

## Release Process

1. **Version Control**
   - Semantic versioning
   - Change documentation
   - Release notes
   - Tag management

2. **Deployment**
   - Staging environment
   - Production deployment
   - Rollback procedures
   - Monitoring
"""
        
        dev_doc_path = self.docs_dir / 'developer_guide.md'
        dev_doc_path.write_text(dev_doc)
        logger.info(f"Developer documentation generated: {dev_doc_path}")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Documentation generator")
    
    parser.add_argument(
        '--type',
        choices=['api', 'user', 'dev', 'all'],
        default='all',
        help='Type of documentation to generate'
    )
    
    args = parser.parse_args()
    
    generator = DocGenerator()
    
    try:
        if args.type in ['api', 'all']:
            generator.generate_api_docs()
        
        if args.type in ['user', 'all']:
            generator.generate_user_guide()
        
        if args.type in ['dev', 'all']:
            generator.generate_developer_docs()
            
        print("Documentation generated successfully")
        
    except Exception as e:
        print(f"Error generating documentation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
