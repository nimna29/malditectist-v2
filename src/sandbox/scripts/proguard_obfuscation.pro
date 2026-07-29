# Aggressive optimization and shrinking to maximize change to the opcode stream
# Obfuscation alone not enough to alters JIT compiled native instructions
# So the optimization + shrinking passes are what actually doing here

-optimizationpasses 5
-overloadaggressively
-repackageclasses ''
-allowaccessmodification
-mergeinterfacesaggressively

# Keep every main() so the JARs remain launchable via java -jar
-keep public class * {

    public static void main(java.lang.String[]);

}

# Keep standard reflection-driven members that break silently if removed
-keepclassmembers class * implements java.io.Serializable {

    static final long serialVersionUID;
    private void writeObject(java.io.ObjectOutputStream);
    private void readObject(java.io.ObjectInputStream);
    
}
-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod


# Do not fail the whole run on unresolved references from thin JARs
-dontwarn
-ignorewarnings


# Silence the duplicate library class notes coming from the jmods module
# and the dynamic reference notes, these are informational only
-dontnote


# Many of these JARs are pre Maven and depend on third party classes that are not bundled inside them
# Such as junit, javax.jms and javax.servlet

# ProGuard optimizer needs the full class hierarchy to verify bytecode
# So an unknown superclass raises IncompleteClassHierarchyException and aborts the run which failed the process
# These options let ProGuard work with a partial hierarchy instead of failing

-dontskipnonpubliclibraryclasses
-dontskipnonpubliclibraryclassmembers
-optimizations !code/allocation/variable

