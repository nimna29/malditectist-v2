# Fallback config for the JAR files that fail the main aggressive config

# Reason was found out - The optimizer needs the full class hierarchy to verify bytecode
# These pre Maven JARs reference third party classes they do not bundle
# So the optimization pass raises IncompleteClassHierarchyException and aborts

# Disabling optimization keeps obfuscation, shrinking and repackaging which still transforms the bytecode
# Just a less aggressively than the main config method

-dontoptimize

-overloadaggressively
-repackageclasses ''
-allowaccessmodification

# Keep every main() so the JARs remain launchable via java -jar
-keep public class * {

    public static void main(java.lang.String[]);

}

# Keep standard reflection driven members that break silently if removed
-keepclassmembers class * implements java.io.Serializable {

    static final long serialVersionUID;
    private void writeObject(java.io.ObjectOutputStream);
    private void readObject(java.io.ObjectInputStream);
    
}
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod

# Do not fail the whole run on unresolved references
-dontwarn
-ignorewarnings
-dontnote