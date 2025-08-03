const path = require('path');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // Override webpack configuration to handle ajv dependency conflicts
      webpackConfig.resolve = {
        ...webpackConfig.resolve,
        fallback: {
          ...webpackConfig.resolve.fallback,
        },
        alias: {
          ...webpackConfig.resolve.alias,
          // Force all ajv imports to use a single version
          'ajv': path.resolve(__dirname, 'node_modules/ajv'),
        }
      };

      // Configure webpack to ignore problematic dependencies
      webpackConfig.ignoreWarnings = [
        /Failed to parse source map/,
        /ajv-keywords/,
        /ajv-formats/,
      ];

      // Modify optimization to avoid terser issues with ajv
      if (webpackConfig.optimization && webpackConfig.optimization.minimizer) {
        webpackConfig.optimization.minimizer = webpackConfig.optimization.minimizer.map(plugin => {
          if (plugin.constructor.name === 'TerserPlugin') {
            plugin.options = {
              ...plugin.options,
              terserOptions: {
                ...plugin.options.terserOptions,
                compress: {
                  ...plugin.options.terserOptions.compress,
                  drop_console: false,
                },
                mangle: {
                  ...plugin.options.terserOptions.mangle,
                  safari10: true,
                },
              },
            };
          }
          return plugin;
        });
      }

      return webpackConfig;
    },
  },
  plugins: [
    {
      plugin: {
        overrideWebpackConfig: ({ webpackConfig }) => {
          // Additional webpack overrides if needed
          return webpackConfig;
        }
      }
    }
  ]
};