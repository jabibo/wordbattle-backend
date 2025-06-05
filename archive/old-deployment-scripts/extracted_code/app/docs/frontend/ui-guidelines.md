# UI/UX Guidelines

## Design Philosophy

WordBattle follows a modern, minimalist design approach that prioritizes usability, accessibility, and visual appeal. The design system emphasizes clarity, consistency, and delightful user interactions.

## Design Principles

### 1. Simplicity First
- Clean, uncluttered interfaces
- Clear visual hierarchy
- Minimal cognitive load
- Focus on essential features

### 2. Consistency
- Unified visual language across all screens
- Consistent interaction patterns
- Standardized spacing and typography
- Predictable navigation

### 3. Accessibility
- High contrast ratios for readability
- Large touch targets (minimum 44px)
- Screen reader compatibility
- Support for dynamic text sizing

### 4. Performance
- Smooth 60fps animations
- Fast loading times
- Responsive interactions
- Efficient memory usage

## Color System

### Primary Colors
```dart
// Primary Blue - Main brand color
static const Color primaryColor = Color(0xFF2196F3);
static const Color primaryLight = Color(0xFF64B5F6);
static const Color primaryDark = Color(0xFF1976D2);

// Secondary Teal - Accent color
static const Color secondaryColor = Color(0xFF03DAC6);
static const Color secondaryLight = Color(0xFF4DD0E1);
static const Color secondaryDark = Color(0xFF00ACC1);
```

### Semantic Colors
```dart
// Success - Green
static const Color successColor = Color(0xFF4CAF50);
static const Color successLight = Color(0xFF81C784);
static const Color successDark = Color(0xFF388E3C);

// Warning - Orange
static const Color warningColor = Color(0xFFFF9800);
static const Color warningLight = Color(0xFFFFB74D);
static const Color warningDark = Color(0xFFF57C00);

// Error - Red
static const Color errorColor = Color(0xFFF44336);
static const Color errorLight = Color(0xFFE57373);
static const Color errorDark = Color(0xFFD32F2F);

// Info - Light Blue
static const Color infoColor = Color(0xFF2196F3);
static const Color infoLight = Color(0xFF64B5F6);
static const Color infoDark = Color(0xFF1976D2);
```

### Dark Theme Colors
```dart
// Background colors
static const Color backgroundColor = Color(0xFF121212);
static const Color surfaceColor = Color(0xFF1E1E1E);
static const Color cardColor = Color(0xFF2C2C2C);

// Text colors
static const Color textPrimary = Color(0xFFFFFFFF);
static const Color textSecondary = Color(0xFFB3B3B3);
static const Color textDisabled = Color(0xFF666666);

// Border colors
static const Color borderColor = Color(0xFF333333);
static const Color dividerColor = Color(0xFF2C2C2C);
```

### Game-Specific Colors
```dart
// Board colors
static const Color boardBackground = Color(0xFF1A1A1A);
static const Color cellDefault = Color(0xFF2C2C2C);
static const Color cellHighlight = Color(0xFF3F51B5);

// Special squares
static const Color tripleWord = Color(0xFFD32F2F);    // Red
static const Color doubleWord = Color(0xFFE91E63);    // Pink
static const Color tripleLetter = Color(0xFF2196F3);  // Blue
static const Color doubleLetter = Color(0xFF03DAC6);  // Teal

// Tile colors
static const Color tileBackground = Color(0xFFFFF8E1);
static const Color tileBorder = Color(0xFFD7CCC8);
static const Color tileText = Color(0xFF3E2723);
```

## Typography

### Font Family
```dart
// Primary font - Roboto (system default)
static const String fontFamily = 'Roboto';

// Monospace font for scores and codes
static const String monospaceFontFamily = 'RobotoMono';
```

### Text Styles
```dart
class AppTextStyles {
  // Headlines
  static const TextStyle headline1 = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.w300,
    letterSpacing: -1.5,
    color: textPrimary,
  );
  
  static const TextStyle headline2 = TextStyle(
    fontSize: 28,
    fontWeight: FontWeight.w300,
    letterSpacing: -0.5,
    color: textPrimary,
  );
  
  static const TextStyle headline3 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w400,
    letterSpacing: 0,
    color: textPrimary,
  );
  
  static const TextStyle headline4 = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w400,
    letterSpacing: 0.25,
    color: textPrimary,
  );
  
  static const TextStyle headline5 = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w400,
    letterSpacing: 0,
    color: textPrimary,
  );
  
  static const TextStyle headline6 = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w500,
    letterSpacing: 0.15,
    color: textPrimary,
  );
  
  // Body text
  static const TextStyle bodyText1 = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w400,
    letterSpacing: 0.5,
    color: textPrimary,
  );
  
  static const TextStyle bodyText2 = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w400,
    letterSpacing: 0.25,
    color: textSecondary,
  );
  
  // Buttons
  static const TextStyle button = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w500,
    letterSpacing: 1.25,
    color: Colors.white,
  );
  
  // Captions and labels
  static const TextStyle caption = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w400,
    letterSpacing: 0.4,
    color: textSecondary,
  );
  
  static const TextStyle overline = TextStyle(
    fontSize: 10,
    fontWeight: FontWeight.w400,
    letterSpacing: 1.5,
    color: textSecondary,
  );
  
  // Game-specific
  static const TextStyle tileText = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w600,
    color: tileText,
    fontFamily: monospaceFontFamily,
  );
  
  static const TextStyle scoreText = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w700,
    color: textPrimary,
    fontFamily: monospaceFontFamily,
  );
}
```

## Spacing System

### Base Unit
```dart
// Base spacing unit (8px)
static const double baseUnit = 8.0;

// Spacing scale
static const double spacing2xs = baseUnit * 0.5;  // 4px
static const double spacingXs = baseUnit * 1;     // 8px
static const double spacingSm = baseUnit * 2;     // 16px
static const double spacingMd = baseUnit * 3;     // 24px
static const double spacingLg = baseUnit * 4;     // 32px
static const double spacingXl = baseUnit * 5;     // 40px
static const double spacing2xl = baseUnit * 6;    // 48px
static const double spacing3xl = baseUnit * 8;    // 64px
```

### Layout Spacing
```dart
class AppSpacing {
  // Screen padding
  static const EdgeInsets screenPadding = EdgeInsets.all(spacingSm);
  static const EdgeInsets screenPaddingHorizontal = EdgeInsets.symmetric(horizontal: spacingSm);
  static const EdgeInsets screenPaddingVertical = EdgeInsets.symmetric(vertical: spacingSm);
  
  // Card padding
  static const EdgeInsets cardPadding = EdgeInsets.all(spacingSm);
  static const EdgeInsets cardPaddingLarge = EdgeInsets.all(spacingMd);
  
  // Button padding
  static const EdgeInsets buttonPadding = EdgeInsets.symmetric(
    horizontal: spacingMd,
    vertical: spacingSm,
  );
  
  static const EdgeInsets buttonPaddingLarge = EdgeInsets.symmetric(
    horizontal: spacingLg,
    vertical: spacingMd,
  );
  
  // List item padding
  static const EdgeInsets listItemPadding = EdgeInsets.symmetric(
    horizontal: spacingSm,
    vertical: spacingXs,
  );
  
  // Input field padding
  static const EdgeInsets inputPadding = EdgeInsets.symmetric(
    horizontal: spacingSm,
    vertical: spacingSm,
  );
}
```

## Component Library

### Buttons

#### Primary Button
```dart
class PrimaryButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isLoading;
  final IconData? icon;
  
  const PrimaryButton({
    Key? key,
    required this.text,
    this.onPressed,
    this.isLoading = false,
    this.icon,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: ElevatedButton(
        onPressed: isLoading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primaryColor,
          foregroundColor: Colors.white,
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        child: isLoading
            ? SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (icon != null) ...[
                    Icon(icon, size: 18),
                    SizedBox(width: 8),
                  ],
                  Text(text, style: AppTextStyles.button),
                ],
              ),
      ),
    );
  }
}
```

#### Secondary Button
```dart
class SecondaryButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final IconData? icon;
  
  const SecondaryButton({
    Key? key,
    required this.text,
    this.onPressed,
    this.icon,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: OutlinedButton(
        onPressed: onPressed,
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.primaryColor,
          side: BorderSide(color: AppColors.primaryColor),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(icon, size: 18),
              SizedBox(width: 8),
            ],
            Text(text, style: AppTextStyles.button.copyWith(
              color: AppColors.primaryColor,
            )),
          ],
        ),
      ),
    );
  }
}
```

### Input Fields

#### Text Input Field
```dart
class AppTextField extends StatelessWidget {
  final String label;
  final String? hint;
  final TextEditingController? controller;
  final String? Function(String?)? validator;
  final TextInputType keyboardType;
  final bool obscureText;
  final IconData? prefixIcon;
  final IconData? suffixIcon;
  final VoidCallback? onSuffixIconTap;
  final bool enabled;
  
  const AppTextField({
    Key? key,
    required this.label,
    this.hint,
    this.controller,
    this.validator,
    this.keyboardType = TextInputType.text,
    this.obscureText = false,
    this.prefixIcon,
    this.suffixIcon,
    this.onSuffixIconTap,
    this.enabled = true,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: AppTextStyles.bodyText2),
        SizedBox(height: 8),
        TextFormField(
          controller: controller,
          validator: validator,
          keyboardType: keyboardType,
          obscureText: obscureText,
          enabled: enabled,
          style: AppTextStyles.bodyText1,
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: AppTextStyles.bodyText2,
            prefixIcon: prefixIcon != null ? Icon(prefixIcon) : null,
            suffixIcon: suffixIcon != null 
                ? IconButton(
                    icon: Icon(suffixIcon),
                    onPressed: onSuffixIconTap,
                  )
                : null,
            filled: true,
            fillColor: AppColors.surfaceColor,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none,
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppColors.primaryColor),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide(color: AppColors.errorColor),
            ),
          ),
        ),
      ],
    );
  }
}
```

### Cards

#### Game Card
```dart
class GameCard extends StatelessWidget {
  final String opponentName;
  final int playerScore;
  final int opponentScore;
  final bool isPlayerTurn;
  final VoidCallback onTap;
  
  const GameCard({
    Key? key,
    required this.opponentName,
    required this.playerScore,
    required this.opponentScore,
    required this.isPlayerTurn,
    required this.onTap,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.symmetric(vertical: 4),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: AppSpacing.cardPadding,
          child: Row(
            children: [
              // Opponent avatar
              CircleAvatar(
                radius: 24,
                backgroundColor: AppColors.primaryColor,
                child: Text(
                  opponentName[0].toUpperCase(),
                  style: AppTextStyles.headline6.copyWith(color: Colors.white),
                ),
              ),
              
              SizedBox(width: 16),
              
              // Game info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'vs $opponentName',
                      style: AppTextStyles.headline6,
                    ),
                    SizedBox(height: 4),
                    Text(
                      '$playerScore - $opponentScore',
                      style: AppTextStyles.bodyText2,
                    ),
                  ],
                ),
              ),
              
              // Turn indicator
              Container(
                padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: isPlayerTurn ? AppColors.primaryColor : AppColors.surfaceColor,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  isPlayerTurn ? 'Your Turn' : 'Their Turn',
                  style: AppTextStyles.caption.copyWith(
                    color: isPlayerTurn ? Colors.white : AppColors.textSecondary,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### Loading States

#### Loading Spinner
```dart
class AppLoadingSpinner extends StatelessWidget {
  final double size;
  final Color? color;
  
  const AppLoadingSpinner({
    Key? key,
    this.size = 24,
    this.color,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CircularProgressIndicator(
        strokeWidth: 2,
        valueColor: AlwaysStoppedAnimation<Color>(
          color ?? AppColors.primaryColor,
        ),
      ),
    );
  }
}
```

#### Loading Overlay
```dart
class LoadingOverlay extends StatelessWidget {
  final bool isLoading;
  final Widget child;
  final String? message;
  
  const LoadingOverlay({
    Key? key,
    required this.isLoading,
    required this.child,
    this.message,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        child,
        if (isLoading)
          Container(
            color: Colors.black54,
            child: Center(
              child: Card(
                child: Padding(
                  padding: EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      AppLoadingSpinner(size: 32),
                      if (message != null) ...[
                        SizedBox(height: 16),
                        Text(message!, style: AppTextStyles.bodyText1),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
```

## Animation Guidelines

### Duration Standards
```dart
class AppAnimations {
  // Standard durations
  static const Duration fast = Duration(milliseconds: 150);
  static const Duration normal = Duration(milliseconds: 300);
  static const Duration slow = Duration(milliseconds: 500);
  
  // Curves
  static const Curve easeIn = Curves.easeIn;
  static const Curve easeOut = Curves.easeOut;
  static const Curve easeInOut = Curves.easeInOut;
  static const Curve bounceIn = Curves.bounceIn;
  static const Curve elasticOut = Curves.elasticOut;
}
```

### Common Animations

#### Fade Transition
```dart
class FadeTransition extends StatelessWidget {
  final Widget child;
  final Duration duration;
  final bool visible;
  
  const FadeTransition({
    Key? key,
    required this.child,
    this.duration = AppAnimations.normal,
    required this.visible,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return AnimatedOpacity(
      opacity: visible ? 1.0 : 0.0,
      duration: duration,
      child: child,
    );
  }
}
```

#### Scale Animation
```dart
class ScaleAnimation extends StatefulWidget {
  final Widget child;
  final Duration duration;
  
  const ScaleAnimation({
    Key? key,
    required this.child,
    this.duration = AppAnimations.normal,
  }) : super(key: key);
  
  @override
  _ScaleAnimationState createState() => _ScaleAnimationState();
}

class _ScaleAnimationState extends State<ScaleAnimation>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: widget.duration,
      vsync: this,
    );
    
    _scaleAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.elasticOut,
    ));
    
    _controller.forward();
  }
  
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _scaleAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _scaleAnimation.value,
          child: widget.child,
        );
      },
    );
  }
}
```

## Accessibility Guidelines

### Color Contrast
- Minimum contrast ratio of 4.5:1 for normal text
- Minimum contrast ratio of 3:1 for large text
- Use semantic colors consistently

### Touch Targets
- Minimum touch target size of 44x44 points
- Adequate spacing between interactive elements
- Clear visual feedback for touch interactions

### Screen Reader Support
```dart
class AccessibleWidget extends StatelessWidget {
  final Widget child;
  final String semanticLabel;
  final String? hint;
  final bool excludeSemantics;
  
  const AccessibleWidget({
    Key? key,
    required this.child,
    required this.semanticLabel,
    this.hint,
    this.excludeSemantics = false,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: semanticLabel,
      hint: hint,
      excludeSemantics: excludeSemantics,
      child: child,
    );
  }
}
```

### Dynamic Text Scaling
```dart
class ResponsiveText extends StatelessWidget {
  final String text;
  final TextStyle style;
  final double maxScaleFactor;
  
  const ResponsiveText({
    Key? key,
    required this.text,
    required this.style,
    this.maxScaleFactor = 1.3,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: style,
      textScaleFactor: math.min(
        MediaQuery.of(context).textScaleFactor,
        maxScaleFactor,
      ),
    );
  }
}
```

## Responsive Design

### Breakpoints
```dart
class AppBreakpoints {
  static const double mobile = 480;
  static const double tablet = 768;
  static const double desktop = 1024;
  
  static bool isMobile(BuildContext context) {
    return MediaQuery.of(context).size.width < mobile;
  }
  
  static bool isTablet(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    return width >= mobile && width < desktop;
  }
  
  static bool isDesktop(BuildContext context) {
    return MediaQuery.of(context).size.width >= desktop;
  }
}
```

### Responsive Layout
```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget? desktop;
  
  const ResponsiveLayout({
    Key? key,
    required this.mobile,
    this.tablet,
    this.desktop,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    if (AppBreakpoints.isDesktop(context) && desktop != null) {
      return desktop!;
    } else if (AppBreakpoints.isTablet(context) && tablet != null) {
      return tablet!;
    } else {
      return mobile;
    }
  }
}
```

## Error States

### Error Message Display
```dart
class ErrorMessage extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;
  final IconData icon;
  
  const ErrorMessage({
    Key? key,
    required this.message,
    this.onRetry,
    this.icon = Icons.error_outline,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: AppSpacing.screenPadding,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 64,
              color: AppColors.errorColor,
            ),
            SizedBox(height: 16),
            Text(
              message,
              style: AppTextStyles.bodyText1,
              textAlign: TextAlign.center,
            ),
            if (onRetry != null) ...[
              SizedBox(height: 24),
              PrimaryButton(
                text: 'Try Again',
                onPressed: onRetry,
                icon: Icons.refresh,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

## Success States

### Success Animation
```dart
class SuccessAnimation extends StatefulWidget {
  final String message;
  final VoidCallback? onComplete;
  
  const SuccessAnimation({
    Key? key,
    required this.message,
    this.onComplete,
  }) : super(key: key);
  
  @override
  _SuccessAnimationState createState() => _SuccessAnimationState();
}

class _SuccessAnimationState extends State<SuccessAnimation>
    with TickerProviderStateMixin {
  late AnimationController _scaleController;
  late AnimationController _fadeController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _fadeAnimation;
  
  @override
  void initState() {
    super.initState();
    
    _scaleController = AnimationController(
      duration: Duration(milliseconds: 600),
      vsync: this,
    );
    
    _fadeController = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );
    
    _scaleAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _scaleController,
      curve: Curves.elasticOut,
    ));
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(_fadeController);
    
    _startAnimation();
  }
  
  void _startAnimation() async {
    await _scaleController.forward();
    await _fadeController.forward();
    
    if (widget.onComplete != null) {
      Future.delayed(Duration(seconds: 2), widget.onComplete);
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          AnimatedBuilder(
            animation: _scaleAnimation,
            builder: (context, child) {
              return Transform.scale(
                scale: _scaleAnimation.value,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: AppColors.successColor,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.check,
                    color: Colors.white,
                    size: 40,
                  ),
                ),
              );
            },
          ),
          SizedBox(height: 24),
          AnimatedBuilder(
            animation: _fadeAnimation,
            builder: (context, child) {
              return Opacity(
                opacity: _fadeAnimation.value,
                child: Text(
                  widget.message,
                  style: AppTextStyles.headline6,
                  textAlign: TextAlign.center,
                ),
              );
            },
          ),
        ],
      ),
    );
  }
  
  @override
  void dispose() {
    _scaleController.dispose();
    _fadeController.dispose();
    super.dispose();
  }
}
```

This comprehensive UI/UX guidelines document provides a solid foundation for creating a consistent, accessible, and visually appealing WordBattle Flutter app. 