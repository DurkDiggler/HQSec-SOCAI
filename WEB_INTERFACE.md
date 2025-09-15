# SOC Agent Web Interface

A modern, responsive web interface for the SOC Agent security operations center. Built with React and FastAPI, it provides real-time monitoring, alert management, and comprehensive analytics.

## 🌟 Features

### Dashboard
- **Real-time Statistics**: Live view of alert counts, severity distribution, and system health
- **Interactive Charts**: Visual representation of alerts over time and severity distribution
- **Recent Alerts**: Quick access to the latest security events
- **System Status**: Health monitoring and service status indicators

### Alert Management
- **Comprehensive Alert List**: View all security alerts with filtering and search
- **Advanced Filtering**: Filter by status, severity, source, category, and custom search terms
- **Status Management**: Update alert status (new, acknowledged, investigating, resolved, false positive)
- **Bulk Operations**: Select and manage multiple alerts simultaneously
- **Real-time Updates**: Live updates as new alerts arrive

### Alert Details
- **Complete Alert Information**: Full details of each security event
- **IOC Analysis**: Indicators of Compromise with threat intelligence data
- **Scoring Breakdown**: Detailed analysis of base and intelligence scores
- **Action History**: Track emails sent and tickets created
- **Raw Data View**: Access to original event data for investigation

### Analytics & Reporting
- **Top Sources**: Most active alert sources
- **Event Type Analysis**: Breakdown of security event types
- **IP Address Tracking**: Most frequently seen IP addresses
- **Trend Analysis**: Historical data and patterns
- **Export Capabilities**: Export data for further analysis

## 🚀 Quick Start

### Option 1: Full Stack with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/SOCAI.git
cd SOCAI

# Run the full stack setup
./setup-full.sh

# Access the web interface
open http://localhost:3000
```

### Option 2: Development Setup

```bash
# Backend setup
cd SOCAI
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Frontend setup
cd frontend
npm install
npm start

# In another terminal, start the backend
cd ..
uvicorn soc_agent.webapp:app --reload
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Database Configuration
DATABASE_URL=postgresql://soc_agent:password@localhost:5432/soc_agent
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=soc_agent
POSTGRES_PASSWORD=your_password
POSTGRES_DB=soc_agent

# API Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1

# Security Settings
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=soc-agent@yourcompany.com
EMAIL_TO=soc@yourcompany.com

# Threat Intelligence APIs
OTX_API_KEY=your-otx-key
VT_API_KEY=your-virustotal-key
ABUSEIPDB_API_KEY=your-abuseipdb-key

# Autotask Configuration
AT_BASE_URL=https://your-instance.autotask.net
AT_API_INTEGRATION_CODE=your-code
AT_USERNAME=your-username
AT_SECRET=your-secret
AT_ACCOUNT_ID=12345
AT_QUEUE_ID=67890
```

## 📱 User Interface

### Dashboard View
- **Statistics Cards**: Key metrics at a glance
- **Charts**: Visual representation of data trends
- **Recent Alerts**: Latest security events
- **System Health**: Service status and performance

### Alerts View
- **Filter Panel**: Advanced filtering options
- **Alert Table**: Comprehensive alert listing
- **Status Management**: Quick status updates
- **Search**: Full-text search across alerts

### Alert Detail View
- **Complete Information**: All alert details
- **IOC Analysis**: Threat intelligence data
- **Scoring Details**: Risk assessment breakdown
- **Action History**: Tracked actions and responses

## 🔌 API Endpoints

### Alerts API
- `GET /api/v1/alerts` - List alerts with filtering
- `GET /api/v1/alerts/{id}` - Get specific alert
- `PATCH /api/v1/alerts/{id}/status` - Update alert status
- `GET /api/v1/alerts/{id}/iocs` - Get alert IOCs

### Statistics API
- `GET /api/v1/statistics` - Get alert statistics
- `GET /api/v1/statistics/sources` - Top alert sources
- `GET /api/v1/statistics/event-types` - Top event types
- `GET /api/v1/statistics/ips` - Top IP addresses
- `GET /api/v1/dashboard` - Complete dashboard data

### Utility API
- `GET /api/v1/health` - Health check
- `GET /api/v1/filters` - Available filter options

## 🎨 Customization

### Themes
The interface supports custom theming through CSS variables:

```css
:root {
  --primary-color: #2563eb;
  --secondary-color: #6b7280;
  --success-color: #059669;
  --warning-color: #d97706;
  --danger-color: #dc2626;
  --background-color: #f8fafc;
  --text-color: #1e293b;
}
```

### Components
All components are modular and can be customized:

- `StatCard` - Statistics display cards
- `Chart` - Data visualization components
- `AlertList` - Alert listing and management
- `AlertDetail` - Individual alert details
- `FilterPanel` - Advanced filtering interface

## 🔒 Security Features

### Authentication
- Optional authentication system
- Role-based access control
- Session management

### Data Protection
- Input validation and sanitization
- XSS protection
- CSRF protection
- Secure API endpoints

### Privacy
- No sensitive data in logs
- Secure data transmission
- Configurable data retention

## 📊 Performance

### Optimization
- **Lazy Loading**: Components loaded on demand
- **Caching**: Intelligent data caching
- **Pagination**: Efficient data loading
- **Real-time Updates**: WebSocket support for live data

### Monitoring
- **Performance Metrics**: Response times and throughput
- **Error Tracking**: Comprehensive error logging
- **Health Checks**: Service availability monitoring
- **Resource Usage**: Memory and CPU monitoring

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### Backend Tests
```bash
pytest tests/ -v --cov=soc_agent
```

### Integration Tests
```bash
pytest tests/test_integration.py -v
```

## 🚀 Deployment

### Production Deployment

1. **Build the application**:
   ```bash
   docker-compose -f docker-compose.full.yml build
   ```

2. **Deploy with environment variables**:
   ```bash
   docker-compose -f docker-compose.full.yml up -d
   ```

3. **Configure reverse proxy** (Nginx/Apache):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3000;
       }
       
       location /api/ {
           proxy_pass http://localhost:8000;
       }
   }
   ```

### Scaling

- **Horizontal Scaling**: Multiple backend instances
- **Database Scaling**: Read replicas and connection pooling
- **Caching**: Redis for session and data caching
- **CDN**: Static asset delivery

## 🔧 Troubleshooting

### Common Issues

1. **Frontend not loading**:
   - Check if backend is running on port 8000
   - Verify CORS configuration
   - Check browser console for errors

2. **Database connection issues**:
   - Verify database credentials
   - Check database server status
   - Review connection string format

3. **API errors**:
   - Check backend logs
   - Verify API endpoint URLs
   - Review request/response format

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Backend
export LOG_LEVEL=DEBUG
uvicorn soc_agent.webapp:app --reload

# Frontend
export REACT_APP_DEBUG=true
npm start
```

## 📈 Monitoring

### Health Checks
- **Backend**: `GET /healthz`
- **Database**: Connection status
- **Frontend**: Service availability

### Metrics
- **Request Count**: API call statistics
- **Response Time**: Performance metrics
- **Error Rate**: Error frequency
- **Active Users**: Concurrent user count

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style
- **Frontend**: ESLint + Prettier
- **Backend**: Black + isort + flake8
- **Testing**: Jest (frontend) + pytest (backend)

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running
- **Component Library**: Storybook documentation
- **Architecture**: System design documents
- **Deployment**: Infrastructure guides

## 🆘 Support

- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Documentation**: Comprehensive guides and tutorials
- **Community**: Discord/Slack channels

---

**The SOC Agent Web Interface provides a powerful, user-friendly way to monitor and manage security alerts with real-time updates, comprehensive analytics, and intuitive management tools.**
