const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const ImageminPlugin = require('imagemin-webpack-plugin').default;
const imageminMozjpeg = require('imagemin-mozjpeg');
const imageminPngquant = require('imagemin-pngquant');
const imageminSvgo = require('imagemin-svgo');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const WorkboxPlugin = require('workbox-webpack-plugin');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // Production optimizations
      if (env === 'production') {
        // Enable tree shaking
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          usedExports: true,
          sideEffects: false,
          splitChunks: {
            chunks: 'all',
            cacheGroups: {
              vendor: {
                test: /[\\/]node_modules[\\/]/,
                name: 'vendors',
                chunks: 'all',
                priority: 10,
              },
              common: {
                name: 'common',
                minChunks: 2,
                chunks: 'all',
                priority: 5,
                reuseExistingChunk: true,
              },
              react: {
                test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
                name: 'react',
                chunks: 'all',
                priority: 20,
              },
              charts: {
                test: /[\\/]node_modules[\\/](recharts)[\\/]/,
                name: 'charts',
                chunks: 'all',
                priority: 15,
              },
              utils: {
                test: /[\\/]node_modules[\\/](axios|date-fns|clsx)[\\/]/,
                name: 'utils',
                chunks: 'all',
                priority: 12,
              }
            }
          },
          minimizer: [
            new TerserPlugin({
              terserOptions: {
                parse: {
                  ecma: 8,
                },
                compress: {
                  ecma: 5,
                  warnings: false,
                  comparisons: false,
                  inline: 2,
                  drop_console: true,
                  drop_debugger: true,
                },
                mangle: {
                  safari10: true,
                },
                output: {
                  ecma: 5,
                  comments: false,
                  ascii_only: true,
                },
              },
              parallel: true,
              extractComments: false,
            }),
          ],
        };

        // Add compression plugin
        webpackConfig.plugins.push(
          new CompressionPlugin({
            algorithm: 'gzip',
            test: /\.(js|css|html|svg)$/,
            threshold: 8192,
            minRatio: 0.8,
          })
        );

        // Add image optimization
        webpackConfig.plugins.push(
          new ImageminPlugin({
            disable: process.env.NODE_ENV !== 'production',
            pngquant: {
              quality: [0.6, 0.8],
            },
            plugins: [
              imageminMozjpeg({
                quality: 80,
                progressive: true,
              }),
              imageminPngquant({
                quality: [0.6, 0.8],
              }),
              imageminSvgo({
                plugins: [
                  {
                    name: 'removeViewBox',
                    active: false,
                  },
                  {
                    name: 'addViewBox',
                    active: true,
                  },
                ],
              }),
            ],
          })
        );

        // Add PWA support
        webpackConfig.plugins.push(
          new WorkboxPlugin.GenerateSW({
            clientsClaim: true,
            skipWaiting: true,
            maximumFileSizeToCacheInBytes: 5000000,
            runtimeCaching: [
              {
                urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
                handler: 'CacheFirst',
                options: {
                  cacheName: 'google-fonts',
                  expiration: {
                    maxEntries: 4,
                    maxAgeSeconds: 365 * 24 * 60 * 60, // 1 year
                  },
                },
              },
              {
                urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
                handler: 'CacheFirst',
                options: {
                  cacheName: 'google-fonts-stylesheets',
                  expiration: {
                    maxEntries: 4,
                    maxAgeSeconds: 365 * 24 * 60 * 60, // 1 year
                  },
                },
              },
              {
                urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/i,
                handler: 'CacheFirst',
                options: {
                  cacheName: 'images',
                  expiration: {
                    maxEntries: 100,
                    maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
                  },
                },
              },
              {
                urlPattern: /^https:\/\/api\./i,
                handler: 'NetworkFirst',
                options: {
                  cacheName: 'api-cache',
                  expiration: {
                    maxEntries: 50,
                    maxAgeSeconds: 5 * 60, // 5 minutes
                  },
                  networkTimeoutSeconds: 3,
                },
              },
            ],
          })
        );

        // Bundle analyzer (only when ANALYZE=true)
        if (process.env.ANALYZE === 'true') {
          webpackConfig.plugins.push(
            new BundleAnalyzerPlugin({
              analyzerMode: 'static',
              openAnalyzer: true,
              reportFilename: 'bundle-report.html',
            })
          );
        }
      }

      // Development optimizations
      if (env === 'development') {
        // Enable source maps for better debugging
        webpackConfig.devtool = 'eval-source-map';
        
        // Optimize development builds
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          splitChunks: {
            chunks: 'all',
            cacheGroups: {
              vendor: {
                test: /[\\/]node_modules[\\/]/,
                name: 'vendors',
                chunks: 'all',
              },
            },
          },
        };
      }

      // Add resolve aliases for better imports
      webpackConfig.resolve.alias = {
        ...webpackConfig.resolve.alias,
        '@': path.resolve(__dirname, 'src'),
        '@components': path.resolve(__dirname, 'src/components'),
        '@pages': path.resolve(__dirname, 'src/pages'),
        '@services': path.resolve(__dirname, 'src/services'),
        '@utils': path.resolve(__dirname, 'src/utils'),
        '@hooks': path.resolve(__dirname, 'src/hooks'),
        '@assets': path.resolve(__dirname, 'src/assets'),
      };

      // Add file extensions
      webpackConfig.resolve.extensions = [
        ...webpackConfig.resolve.extensions,
        '.js',
        '.jsx',
        '.ts',
        '.tsx',
        '.json',
      ];

      return webpackConfig;
    },
  },
  devServer: {
    port: 3000,
    hot: true,
    compress: true,
    historyApiFallback: true,
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
    // Enable gzip compression in development
    setupMiddlewares: (middlewares, devServer) => {
      if (!devServer) {
        throw new Error('webpack-dev-server is not defined');
      }
      return middlewares;
    },
  },
  babel: {
    plugins: [
      // Add babel plugins for optimization
      ['@babel/plugin-transform-runtime', {
        corejs: false,
        helpers: true,
        regenerator: true,
        useESModules: false,
      }],
    ],
  },
};
