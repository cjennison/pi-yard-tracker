# Pi Yard Tracker Frontend

A modern, responsive web interface for the Pi Yard Tracker wildlife monitoring system. Built with React, TypeScript, and Mantine UI components for a slick user experience.

## 🚀 Features

### 🎨 Modern UI/UX

- **Dark/Light Mode**: Automatic theme switching with system preference detection
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Smooth Animations**: Hover effects, page transitions, and loading states
- **Accessibility**: WCAG compliant with focus management and screen reader support

### 📊 Dashboard

- **Real-time Statistics**: Auto-refreshing stats every 5 seconds
- **Interactive Timeline**: Activity visualization with multiple time ranges (24h, 7d, 30d)
- **Detection Heatmap**: Hourly activity patterns throughout the day
- **Distribution Charts**: Donut and bar charts for detection analysis
- **Recent Activity Feed**: Latest detections with timestamps

### 📷 Photo Gallery

- **Grid Layout**: Responsive photo grid with hover effects
- **Advanced Filtering**: Search, date range, detection count filters
- **Modal Viewer**: Full-screen photo viewing with detection details
- **Lazy Loading**: Optimized image loading for performance
- **Batch Operations**: Download and manage multiple photos

### 🎯 Detection Analysis

- **Sortable Table**: Interactive table with sortable columns
- **Confidence Visualization**: Progress bars and color-coded confidence levels
- **Advanced Filters**: Class-based filtering with confidence range sliders
- **Bounding Box Details**: Precise object location information
- **Detection Timeline**: Track detection patterns over time

### 📡 Live Camera View

- **Real-time Stream**: WebSocket-based live camera feed
- **Detection Overlays**: Real-time bounding boxes with confidence scores
- **Performance Stats**: FPS, processing time, and detection metrics
- **Interactive Controls**: Toggle overlays, adjust confidence thresholds
- **Activity Monitor**: Live detection feed with recent activity log

## 🛠 Tech Stack

- **React 18**: Latest React with hooks and concurrent features
- **TypeScript**: Type-safe development with excellent IDE support
- **Mantine v8**: Modern React components library with excellent UX
- **React Query**: Server state management with caching and synchronization
- **React Router**: Client-side routing with lazy loading
- **Recharts**: Interactive charts and data visualization
- **Axios**: HTTP client with interceptors and error handling
- **Day.js**: Lightweight date/time manipulation
- **Vite**: Fast build tool with hot module replacement

## 🎨 Design System

### Color Palette

- **Primary**: Green tones for nature/wildlife theme
- **Secondary**: Blue for interface elements
- **Accent**: Orange for highlights and warnings
- **Status Colors**: Semantic colors for success, warning, error states

### Typography

- **Headers**: Inter font family for clean, modern look
- **Body**: System fonts for optimal readability
- **Monospace**: Code and data display

### Layout

- **Sidebar Navigation**: Collapsible sidebar with contextual stats
- **Card-based UI**: Consistent card layouts with shadows and borders
- **Grid System**: Responsive 12-column grid with breakpoints
- **Spacing**: Consistent spacing scale (xs, sm, md, lg, xl)

## 📱 Responsive Breakpoints

```css
xs: 0px      /* Mobile portrait */
sm: 576px    /* Mobile landscape */
md: 768px    /* Tablet */
lg: 992px    /* Desktop */
xl: 1200px   /* Large desktop */
```

## 🔧 Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server (NOT recommended for Raspberry Pi - too memory intensive)
npm run dev

# Build for production
npm run build

# Serve production build (RECOMMENDED for Raspberry Pi - low memory usage)
cd dist
python3 -m http.server 5173

# Preview production build (alternative using Vite)
npm run preview
```

### Project Structure

```
src/
├── api/                 # API client and hooks
│   ├── client.ts       # Axios configuration
│   ├── hooks.ts        # React Query hooks
│   └── types.ts        # TypeScript interfaces
├── components/         # Reusable components
│   ├── ErrorBoundary/  # Error handling
│   ├── Layout/         # App shell layout
│   └── Loading/        # Loading states
├── pages/              # Page components
│   ├── Dashboard/      # Main dashboard
│   ├── Photos/         # Photo gallery
│   ├── Detections/     # Detection analysis
│   └── LiveView/       # Live camera feed
├── App.tsx             # Root component
├── theme.ts            # Mantine theme config
└── routes.tsx          # React Router config
```

## 🎯 UX Features

### Performance Optimizations

- **Code Splitting**: Route-based lazy loading
- **Image Optimization**: WebP support with fallbacks
- **Caching**: React Query caching with background updates
- **Debouncing**: Search input debouncing for better performance
- **Virtualization**: Large lists rendered efficiently

### Accessibility

- **Keyboard Navigation**: Full keyboard support
- **Focus Management**: Proper focus trapping in modals
- **Screen Reader**: ARIA labels and semantic HTML
- **Color Contrast**: WCAG AA compliant color ratios
- **Reduced Motion**: Respects user's motion preferences

### Error Handling

- **Error Boundaries**: Graceful error recovery
- **Network Errors**: Retry mechanisms with exponential backoff
- **User Feedback**: Toast notifications for actions
- **Offline Support**: Basic offline functionality with service workers

### Loading States

- **Skeleton Screens**: Content-aware loading placeholders
- **Progressive Loading**: Incremental content loading
- **Spinners**: Context-appropriate loading indicators
- **Progress Bars**: For long-running operations

## 🚀 Getting Started

### For Raspberry Pi (Recommended)

1. **Start the backend server** (ensure it's running on port 8000)

   ```bash
   cd /home/cjennison/src/pi-yard-tracker
   source venv/bin/activate
   uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
   ```

2. **Build the frontend** (one time, or after code changes)

   ```bash
   cd frontend
   npm run build
   ```

3. **Serve the production build**

   ```bash
   cd dist
   python3 -m http.server 5173
   ```

4. **Open browser**: Navigate to `http://localhost:5173`

The frontend will connect to the API at `http://localhost:8000` and display real-time wildlife detection data.

### For Development Machine (Laptop/Desktop)

1. **Start the backend server** (ensure it's running on port 8000)
2. **Install frontend dependencies**: `npm install`
3. **Start development server**: `npm run dev`
4. **Open browser**: Navigate to `http://localhost:5173`

## 🔮 Future Enhancements

- **PWA Support**: Offline functionality and app installation
- **Push Notifications**: Real-time detection alerts
- **Export Features**: CSV/PDF export for reports
- **Advanced Filters**: Machine learning-based filtering
- **Video Playback**: Recorded video clips of detections
- **Map Integration**: Geographic detection mapping

---

Built with ❤️ for wildlife enthusiasts and technology lovers!
